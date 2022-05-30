from __future__ import annotations

import os

from typing import Callable

from distributed import Future, LocalCluster
from distributed import Client
from distributed import get_client
from distributed.scheduler import TaskState


from .delegate import Delegate
from .delegate import JobState
from .delegate import JobStatus
from .delegate import DelegateConfig

from stochss_compute.api.cache import CacheProvider
from stochss_compute.api.cache import SimpleDiskCache
from stochss_compute.api.cache import SimpleDiskCacheConfig

class DaskDelegateConfig(DelegateConfig):

    dask_cluster_port = 8786
    dask_cluster_address = "localhost"

    dask_kwargs = None

    cache_provider: type[CacheProvider] = SimpleDiskCache(SimpleDiskCacheConfig())


class DaskDelegate(Delegate):
    type: str = "dask"

    def __init__(self, delegate_config: DaskDelegateConfig):
        super()

        self.delegate_config = delegate_config
        self.cache_provider = self.delegate_config.cache_provider

        # Attempt to load the global Dask client.
        try:
            self.client = get_client()

        except ValueError as _:

            if self.delegate_config.dask_kwargs is not None:
                dask_cluster = LocalCluster(**self.delegate_config.dask_kwargs)
                self.client = Client(dask_cluster)
            else:
                self.client = Client(f"{self.delegate_config.dask_cluster_address}:{self.delegate_config.dask_cluster_port}")
            
        print(f"Connected to Dask Scheduler:\n{self.client}")

        # Setup functions to be run on the schedule.
        def __scheduler_job_exists(dask_scheduler, job_id: str) -> bool:
            return job_id in dask_scheduler.tasks

        def __scheduler_job_state(dask_scheduler, job_id: str) -> TaskState:
            return dask_scheduler.tasks[job_id].state

        self.scheduler_job_exists = __scheduler_job_exists
        self.scheduler_job_state = __scheduler_job_state

    def __job_state(self, job_id: str) -> TaskState:
        return self.client.run_on_scheduler(self.scheduler_job_state, job_id=job_id)

    def connect(self) -> bool:
        # No need to connect.
        return True

    def test_connection(self) -> bool:
        # Shim this out until I figure out a good way to test a Dask and Redis connection.
        return True

    def create_job(self, job_id: str) -> bool:
        # No concept of creating a job.
        return True

    def start_job(self, job_id: str, work: Callable, *args, **kwargs) -> bool:
        if self.job_exists(job_id) or self.job_complete(job_id):
            return False

        # Parse and replace instances of the internal `result://` proxy protocol.
        # In short, this allows for callees to reference an in-progress or remote job without needing direct access.
        function_args = [(self.client.get_dataset(arg.replace("result://", "")) if isinstance(arg, str) and arg.startswith("result://") else arg) for arg in args]

        # Create a job to run the desired function.
        job_future: Future = self.client.submit(work, *function_args, **kwargs, key=job_id, pure=False)

        # Start additional cache job which depends on the results of the previous.
        cache_future: Future = self.client.submit(self.cache_provider.put, *[job_id, job_future], pure=False)

        # Publish the job as a dataset to maintain state across requests.
        self.client.publish_dataset(job_future, name=job_id, override=True)
        self.client.publish_dataset(cache_future, override=True)

        return True

    def stop_job(self, job_id: str) -> bool:
        if not self.job_exists(job_id):
            return False

        try:
            # Iterate through the dependencies of this job.
            dependencies = self.client.run_on_scheduler(lambda dask_scheduler: [(state.key) for state in dask_scheduler.tasks[id].dependencies])

            # Filter out any weak depenencies. Strong dependencies are suffixed with "/" and the name of the job.
            dependencies = [(dependency) for dependency in dependencies if dependency.replace(id, "").startswith("/")]

            futures = [(Future(key)) for key in dependencies]
            futures.append(Future(job_id))
        except KeyError:
            # do nothing if no dependencies
            pass

        self.client.cancel(Future(job_id))
        self.client.unpublish_dataset(job_id)

        # Hacky fix -- Simulation processes continue executing EVEN IF the parent task is killed.
        def hacky():
            os.system("pkill -f 'Simulation.out'")

        self.client.run(hacky, nanny=True)

        return True

    def job_status(self, job_id: str) -> JobStatus:
        # If the job is complete (results exist as a dataset or in the vault).
        if self.job_complete(job_id):
            status = JobStatus()
            status.status_id = JobState.DONE
            status.status_text = "The job is complete."
            status.has_failed = False
            status.is_done = True

            return status

        # If the job doesn't exist.
        if not self.job_exists(job_id):
            status = JobStatus()
            status.status_id = JobState.DOES_NOT_EXIST
            status.status_text = f"A job with job_id: '{job_id}' does not exist."
            status.has_failed = True
            status.is_done = False

            return status

        status_mapping = {
            "released": (JobState.STOPPED, "The job is known but not actively computing or in memory."),
            "waiting": (JobState.WAITING, "The job is ready to be computed but is waiting for dependencies to arrive in worker memory."),
            "no-worker": (JobState.WAITING, "The job is ready to be computed but is waiting for a worker to become available."),
            "processing": (JobState.RUNNING, "The job is running."),
            "memory": (JobState.DONE, "The job is done and is being held in memory."),
            "erred": (JobState.FAILED, "The job has failed."),
            "done": (JobState.DONE, "The job is done and has been cached / stored on disk.")
        }

        # Grab the task state from the scheduler.
        future_status = self.__job_state(job_id)

        status = JobStatus()
        status.status_id = status_mapping[future_status][0]
        status.status_text = status_mapping[future_status][1]

        status.is_done = status.status_id is JobState.DONE
        status.has_failed = status.status_id is JobState.FAILED

        return status

    def job_results(self, job_id: str):
        # The results of this job may exist on the client dataset.
        if job_id in self.client.datasets:
            print("[DEBUG] Getting results from dataset.")
            return self.client.get_dataset(name=job_id).result()

        # If the results are not in the cache, raise an exception.
        if not self.cache_provider.exists(job_id):
            raise Exception(f"Result with ID '{job_id}' does not exist in the cache.")

        return self.cache_provider.get(job_id)

    def job_complete(self, job_id: str) -> bool:
        # Finished job results must exist within the cache for it to be considered 'done'.
        return self.cache_provider.exists(job_id)

    def job_exists(self, job_id: str) -> bool:
        # Check if the job exists in the scheduler.
        return self.client.run_on_scheduler(self.scheduler_job_exists, job_id=job_id)

    def get_remote_dependency(self, dependency_id: str):
        # Check to see if the job exists as a dataset.
        dependency = self.client.get_dataset(name=dependency_id)

        if dependency is not None:
            return dependency

        raise Exception("Something broke, dependency does not exist within distributed memory.")
