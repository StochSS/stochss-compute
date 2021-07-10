import dill

from pathlib import Path
from typing import Callable

from redis import Redis
from dask.distributed import Future
from dask.distributed import Client
from dask.distributed import fire_and_forget

from stochss_compute.api.delegate.delegate import Delegate
from stochss_compute.api.delegate.delegate import JobState
from stochss_compute.api.delegate.delegate import JobStatus
from stochss_compute.api.delegate.delegate import DelegateConfig

class DaskDelegateConfig(DelegateConfig):
    redis_port = 6379
    redis_address = "0.0.0.0"
    redis_db = 0
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
        self.vault_dir = delegate_config.redis_vault_dir
        self.cluster_address = f"tcp://{delegate_config.dask_cluster_address}:{delegate_config.dask_cluster_port}"

        # Connect to the Redis DB.
        self.redis = Redis(
            host=delegate_config.redis_address,
            port=delegate_config.redis_port,
            db=delegate_config.redis_db
        )

    def __cache_results(self, future: Future):
        # This function will be fired on the Dask worker after the job is complete.
        # It will save the results in the Redis cache.
        result = dill.dumps(future.result())
        
        # Save the results on Disk, store the path in Redis.
        outpath = Path(self.vault_dir).joinpath(future.key)
        with outpath.open("w+b") as outfile:
            outfile.write(result)

        self.redis.set(f"{future.key}", str(outpath.resolve()))
        self.redis.save()

    def connect(self) -> bool:
        # No need to connect.
        return True

    def test_connection(self) -> bool:
        # Shim this out until I figure out a good way to test a Dask and Redis connection.
        self.redis.ping()

        return True

    def create_job(self, id: str) -> bool:
        # No concept of creating a job.
        return True

    def start_job(self, id: str, work: Callable, *args, **kwargs) -> bool:
        if self.job_exists(id) or self.job_complete(id):
            return False

        # Initialize the Dask client and connect to the specified cluster.
        client = Client(self.cluster_address)
        
        # Create a job and set a callback to cache the results once complete.
        job_future: Future = client.submit(work, key=id)
        job_future.add_done_callback(self.__cache_results)
 
        # Fire-and-forget the Future. This ensures that the job continues even
        # if we don't keep the object around.
        # Note: Once the job is complete it's removed from worker memory.
        fire_and_forget(job_future)

        # Create the state value in Redis.
        self.redis.set(f"state-{id}", "no-worker")

        return True

    def stop_job(self, id: str) -> bool:
        if not self.job_exists(id):
            return False

        return True

    def job_status(self, id: str) -> JobStatus:
        # The job may exist in the cache.
        if self.job_complete(id):
            status = JobStatus()
            status.status_id = JobState.DONE
            status.status_text = "The job is complete."
            status.has_failed = False
            status.is_done = True

            return status

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
            "done": (JobState.DONE, "The job is done and is stored on disk.")
        }

        future_status = self.redis.get(f"state-{id}").decode("utf-8")

        status = JobStatus()
        status.status_id = status_mapping[future_status][0]
        status.status_text = status_mapping[future_status][1]

        status.is_done = status.status_id is JobState.DONE
        status.has_failed = status.status_id is JobState.FAILED

        return status

    def job_results(self, id: str):
        # Results are stored and recieved from the Redis cache.
        results_file = self.redis.get(f"{id}")

        with open(results_file, "rb") as infile:
            results = dill.load(infile)

        print(f"Getting cached results from file {results_file}.")
        return results

    def job_complete(self, id: str) -> bool:
        return self.redis.get(f"state-{id}") == "done"

    def job_exists(self, id: str) -> bool:
        return self.redis.get(f"state-{id}") is not None

