import dill

from pathlib import Path
from typing import Callable

from redis import Redis
from distributed import Future
from distributed import Client
from distributed import get_client
from distributed import fire_and_forget

from .delegate import Delegate
from .delegate import JobState
from .delegate import JobStatus
from .delegate import DelegateConfig

from .redis_namespace import vault_prefix
from .redis_namespace import cache_prefix
from .redis_namespace import state_prefix

import os

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

    def __cache_results(self, future: Future):
        # This function will be fired on the Dask worker after the job is complete.
        # It will save the results in the Redis cache.
        result = dill.dumps(future.result())

        # Cache the results for a specified TTL (in seconds).
        self.redis.set(cache_prefix(future.key), result, ex=self.delegate_config.redis_cache_ttl)

        # Save the results on Disk, store the path in Redis.
        outpath = Path(self.delegate_config.redis_vault_dir).joinpath(future.key)

        if not outpath.parent.is_dir():
            outpath.parent.mkdir()

        with outpath.open("w+b") as outfile:
            outfile.write(result)

        self.redis.set(vault_prefix(future.key), str(outpath.resolve()))

        # Close the Client that started this job.
        with get_client() as client:
            client.close()

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
        self.redis.set(state_prefix(id), "no-worker")

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
            "done": (JobState.DONE, "The job is done and has been cached / stored on disk.")
        }

        future_status = self.redis.get(state_prefix(id)).decode("utf-8")

        status = JobStatus()
        status.status_id = status_mapping[future_status][0]
        status.status_text = status_mapping[future_status][1]

        status.is_done = status.status_id is JobState.DONE
        status.has_failed = status.status_id is JobState.FAILED

        return status

    def job_results(self, id: str):
        # If the result is still cached, return it directly from memory.
        cached_results = self.redis.get(cache_prefix(id))

        if cached_results is not None:
            print(f"Getting results from cache.")
            return dill.loads(cached_results)

        # If the results are not in the cache, return from the disk.
        results_file = self.redis.get(vault_prefix(id)).decode("utf-8")

        with open(results_file, "rb") as infile:
            results = dill.load(infile)

        print(f"Getting vaulted results from {results_file}.")
        return results

    def job_complete(self, id: str) -> bool:
        redis_val = self.redis.get(state_prefix(id))

        return redis_val is not None and redis_val.decode("utf-8") == "done"

    def job_exists(self, id: str) -> bool:
        return self.redis.get(state_prefix(id)) is not None

