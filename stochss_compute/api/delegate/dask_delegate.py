import dill

from pathlib import Path
from typing import Callable

from redis import Redis
from distributed import Future
from distributed import Client
from distributed import Variable
from distributed import get_client

from .delegate import Delegate
from .delegate import JobState
from .delegate import JobStatus
from .delegate import DelegateConfig

from .redis_namespace import vault_prefix
from .redis_namespace import cache_prefix
from .redis_namespace import state_prefix

class DaskDelegateConfig(DelegateConfig):
    redis_port = 6379
    redis_address = "0.0.0.0"
    redis_db = 0

    redis_cache_ttl = 60 * 60
    redis_vault_dir = "vault"

    dask_cluster_port = 8786
    dask_cluster_address = "localhost"
    dask_use_remote_cluster = False

    dask_worker_count = 1
    dask_worker_threads = 2
    dask_worker_memory_limit = "4GB"

    dask_dashboard_port = 8788
    dask_dashboard_address = "localhost"
    dask_dashboard_enabled = False

class DaskDelegate(Delegate):
    type: str = "dask"

    def __init__(self, delegate_config: DaskDelegateConfig):
        self.cluster_address = f"tcp://{delegate_config.dask_cluster_address}:{delegate_config.dask_cluster_port}"
        self.delegate_config = delegate_config

        # Connect to the Redis DB.
        self.redis = Redis(
            host=delegate_config.redis_address,
            port=delegate_config.redis_port,
            db=delegate_config.redis_db
        )

        # Attempt to load the global Dask client.
        try:
            self.client = get_client()
        except:
            self.client = Client(self.cluster_address)

        # Setup functions to be run on the schedule.
        def __scheduler_job_exists(dask_scheduler, id):
            return id in dask_scheduler.tasks

        def __scheduler_job_state(dask_scheduler, id):
            return dask_scheduler.tasks[id].state

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

    def __job_state(self, id: str):
        return self.client.run_on_scheduler(self.scheduler_job_state, id=id)

    def connect(self) -> bool:
        # No need to connect.
        return True

    def test_connection(self) -> bool:
        # Shim this out until I figure out a good way to test a Dask and Redis connection.
        return True

    def create_job(self, id: str) -> bool:
        # No concept of creating a job.
        return True

    def start_job(self, id: str, work: Callable, *args, **kwargs) -> bool:
        if self.job_exists(id) or self.job_complete(id):
            return False

        # Parse *args and **kwargs for references to remote data.
        function_args = [(self.client.get_dataset(arg.replace("result://", "")) if isinstance(arg, str) and arg.startswith("result://") else arg) for arg in args]

        # Create a job and set a callback to cache the results once complete.
        job_future: Future = self.client.submit(work, *function_args, **kwargs, key=id, pure=False)
        # job_future.add_done_callback(self.__cache_results)

        # Publish the job as a dataset to maintain state across requests.
        self.client.publish_dataset(job_future, name=id, override=True)

        return True

    def stop_job(self, id: str) -> bool:
        if not self.job_exists(id):
            return False

        # Iterate through the dependencies of this job.
        dependencies = self.client.run_on_scheduler(lambda dask_scheduler: [(state.key) for state in dask_scheduler.tasks[id].dependencies])

        # Filter out any weak depenencies. Strong dependencies are suffixed with "/" and the name of the job.
        dependencies = [(dependency) for dependency in dependencies if dependency.replace(id, "").startswith("/")]

        futures = [(Future(key)) for key in dependencies]
        futures.append(Future(id))

        self.client.cancel(futures)
        self.client.unpublish_dataset(id)

        return True

    def job_status(self, id: str) -> JobStatus:
        # If the job is complete (results exist as a dataset or in the vault).
        if self.job_complete(id):
            status = JobStatus()
            status.status_id = JobState.DONE
            status.status_text = "The job is complete."
            status.has_failed = False
            status.is_done = True

            return status

        # If the job doesn't exist.
        if not self.job_exists(id):
            status = JobStatus()
            status.status_id = JobState.DOES_NOT_EXIST
            status.status_text = f"A job with id: '{id}' does not exist."
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
        future_status = self.__job_state(id)

        status = JobStatus()
        status.status_id = status_mapping[future_status][0]
        status.status_text = status_mapping[future_status][1]

        status.is_done = status.status_id is JobState.DONE
        status.has_failed = status.status_id is JobState.FAILED

        return status

    def job_results(self, id: str):
        # The results of this job may exist on the client dataset.
        result_dataset = self.client.get_dataset(name=id).result()

        if result_dataset is not None:
            print(f"[DEBUG] Getting results from dataset.")
            return result_dataset

        # If the results are not in the cache, return from the disk.
        results_file = Path(self.delegate_config.redis_vault_dir, id)

        if not results_file.is_file():
            raise Exception(f"Results file '{results_file} does not exist in the vault.")

        print(f"[DEBUG] Getting vaulted results from {results_file}.")
        return dill.loads(results_file.read_bytes())

    def job_complete(self, id: str) -> bool:
        # Finished jobs must exist in the Vault (even if they exist within Redis or as a dataset).
        return Path(self.delegate_config.redis_vault_dir, id).is_file()

    def job_exists(self, id: str) -> bool:
        # Check if the job exists in the scheduler.
        return self.client.run_on_scheduler(self.scheduler_job_exists, id=id)

