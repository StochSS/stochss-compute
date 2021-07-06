import dill

from typing import Callable

from redis import Redis
from dask.distributed import Future
from dask.distributed import Client
from dask.distributed import LocalCluster

from stochss_compute.api.delegate.delegate import Delegate
from stochss_compute.api.delegate.delegate import JobState
from stochss_compute.api.delegate.delegate import JobStatus
from stochss_compute.api.delegate.delegate import DelegateConfig

class DaskDelegateConfig(DelegateConfig):
    redis_port = 6379
    redis_address = "redis"
    redis_db = 0

    dask_cluster_port = 4467
    dask_cluster_address = 4467
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
        if delegate_config.dask_use_remote_cluster:
            raise Exception("Remote dask clusters are not supported.")

        self.task_map: dict[str, Future] = { }
        self.cluster = LocalCluster(
            dashboard_address=f"{delegate_config.dask_dashboard_address}:{delegate_config.dask_dashboard_port}",
            n_workers=delegate_config.dask_worker_count,
            threads_per_worker=delegate_config.dask_worker_threads,
            memory_limit=delegate_config.dask_worker_memory_limit
        )

        # Initialize the Dask client and connect to the specified cluster.
        self.client = Client(self.cluster)

        # Connect to the Redis DB.
        self.redis = Redis(
            host=delegate_config.redis_address,
            port=delegate_config.redis_port,
            db=delegate_config.redis_db
        )

    def __cache_results(self, future: Future):
        # future: Future = dill.loads(self.redis.get(id))
        future = self.task_map[future.key]
        result = future.result()

        self.redis.set(f"{future.key}", dill.dumps(result))
        self.redis.save()

        print(f"Task with ID {future.key} has been cached.")

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
        if self.job_exists(id):
            return False

        # Create a job and set a callback to cache the results once complete.
        job_future: Future = self.client.submit(work, key=id)
        job_future.add_done_callback(self.__cache_results)

        # We use a local dict to map ID, Future pairs. While this is not as robust as other methods,
        # Dask will not run a task unless it exists within the Client's parent.
        self.task_map[id] = job_future

        return True

    def stop_job(self, id: str) -> bool:
        if not self.job_exists(id):
            return False

        # dill.loads(self.redis.get(id)).cancel()
        self.task_map[id].cancel()

        return True

    def job_status(self, id: str) -> JobStatus:
        if not self.job_exists(id):
            status = JobStatus()
            status.status_id = JobState.DOES_NOT_EXIST
            status.status_text = f"A job with id: '{id}' does not exist."
            status.has_failed = True
            status.is_done = False

            return status

        status_mapping = {
            "cancelled": (JobState.STOPPED, "The job has been cancelled."),
            "finished": (JobState.DONE, "The job is complete."),
            "lost": (JobState.FAILED, "The job was lost."),
            "pending": (JobState.RUNNING, "The job is running."),
            "error": (JobState.FAILED, "The job has failed.")
        }

        # job_future: Future = dill.loads(self.redis.get(id))
        job_future = self.task_map[id]
        future_status = job_future.status

        status = JobStatus()
        status.status_id = status_mapping[future_status][0]
        status.status_text = status_mapping[future_status][1]

        status.is_done = status.status_id is JobState.DONE
        status.has_failed = status.status_id is JobState.FAILED

        return status

    def job_results(self, id: str):
        # Results are stored and recieved from the Redis cache.
        redis_results = self.redis.get(f"{id}")

        if redis_results is not None:
            print("Getting cached results.")
            return dill.loads(redis_results)

    def job_exists(self, id: str) -> bool:
        # return self.redis.get(id) is not None
        return id in self.task_map

