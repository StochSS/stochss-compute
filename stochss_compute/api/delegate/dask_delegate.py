import os

from pathlib import Path
from typing import Callable

import dill

from distributed import Future
from distributed import Client
from distributed import get_client
from distributed.scheduler import TaskState

from dask_kubernetes import KubeCluster

from .delegate import Delegate
from .delegate import JobState
from .delegate import JobStatus
from .delegate import DelegateConfig

class DaskDelegateConfig(DelegateConfig):
    redis_port = 6379
    redis_address = os.environ.get("REDIS_ADDRESS")
    redis_db = 0

    redis_cache_ttl = 60 * 60
    redis_vault_dir = "vault"

    dask_cluster_port = 8786
    dask_cluster_address = os.environ.get("DASK_SCHEDULER_ADDRESS")
    dask_use_remote_cluster = False

    dask_worker_count = 1
    dask_worker_threads = 2
    dask_worker_memory_limit = "4GB"

    dask_dashboard_port = 8788
    dask_dashboard_address = "localhost"
    dask_dashboard_enabled = False

    dask_worker_spec = os.environ.get("WORKER_SPEC_PATH")

class DaskDelegate(Delegate):
    type: str = "dask"

    def __init__(self, delegate_config: DaskDelegateConfig):

        super()
        self.delegate_config = delegate_config
        # cluster.adapt(minimum=1, maximum=3)
        # print(self.client.address)

        # # Attempt to load the global mDask client.
        try:
            self.client = get_client()
        except ValueError as _:
            cluster = KubeCluster(pod_template= self.delegate_config.dask_worker_spec, n_workers = 1)
            cluster.adapt(minimum=1, maximum=7)
            self.client = Client(cluster)
            
            print(cluster)
            # self.client = Client(self.cluster_address)

        # Setup functions to be run on the schedule.
        def __scheduler_job_exists(dask_scheduler, job_id: str) -> bool:
            return job_id in dask_scheduler.tasks

        def __scheduler_job_state(dask_scheduler, job_id: str) -> TaskState:
            return dask_scheduler.tasks[job_id].state

        self.scheduler_job_exists = __scheduler_job_exists
        self.scheduler_job_state = __scheduler_job_state

    def __cache_results(self, future: Future):
        # Save the results in the vault.
        outpath = Path(self.delegate_config.redis_vault_dir).joinpath(future.key)

        if not outpath.parent.is_dir():
            outpath.parent.mkdir()

        with outpath.open("w+b") as outfile:
            result = dill.dumps(future.result())
            outfile.write(result)

    def __job_state(self, job_id: str) -> TaskState:
        return self.client.run_on_scheduler(self.scheduler_job_state, id=job_id)

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

        # Initialize the Dask client and connect to the specified cluster.
        # cluster = KubeCluster(self.delegate_config.dask_worker_spec)
        # cluster.adapt(minimum=1, maximum=3)
        # self.client = Client(cluster)
        
        # Parse *args and **kwargs for references to remote data.
        function_args = [(self.client.get_dataset(arg.replace("result://", "")) if isinstance(arg, str) and arg.startswith("result://") else arg) for arg in args]

        # Create a job and set a callback to cache the results once complete.
        job_future: Future = self.client.submit(work, *function_args, **kwargs, key=job_id, pure=False)
        job_future.add_done_callback(self.__cache_results)

        # Publish the job as a dataset to maintain state across requests.
        self.client.publish_dataset(job_future, name=job_id, override=True)

        return True

    def stop_job(self, job_id: str) -> bool:
        if not self.job_exists(job_id):
            return False

        # Iterate through the dependencies of this job.
        dependencies = self.client.run_on_scheduler(lambda dask_scheduler: [(state.key) for state in dask_scheduler.tasks[id].dependencies])

        # Filter out any weak depenencies. Strong dependencies are suffixed with "/" and the name of the job.
        dependencies = [(dependency) for dependency in dependencies if dependency.replace(id, "").startswith("/")]

        futures = [(Future(key)) for key in dependencies]
        futures.append(Future(job_id))

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
            "waiting": (JobState.WAITING, "The job is waiting for dependencies to arrive in memory."),
            "no-worker": (JobState.WAITING, "The job is waiting for a worker to become available."),
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
        result_dataset = self.client.get_dataset(name=job_id).result()

        if result_dataset is not None:
            print("[DEBUG] Getting results from dataset.")
            return result_dataset

        # If the results are not in the cache, return from the disk.
        results_file = Path(self.delegate_config.redis_vault_dir, job_id)

        if not results_file.is_file():
            raise Exception(f"Results file '{results_file} does not exist in the vault.")

        print(f"[DEBUG] Getting vaulted results from {results_file}.")
        return dill.loads(results_file.read_bytes())

    def job_complete(self, job_id: str) -> bool:
        # Finished jobs must exist in the Vault (even if they exist within Redis or as a dataset).
        return Path(self.delegate_config.redis_vault_dir, job_id).is_file()

    def job_exists(self, job_id: str) -> bool:
        # Check if the job exists in the scheduler.
        return self.client.run_on_scheduler(self.scheduler_job_exists, job_id=job_id)
