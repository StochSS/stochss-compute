import dill

from typing import Callable

from redis import Redis
from dask.distributed import Future
from dask.distributed import Client
from dask.distributed import LocalCluster
from dask.distributed import fire_and_forget

from stochss_compute.api.delegate.delegate import Delegate
from stochss_compute.api.delegate.delegate import JobState
from stochss_compute.api.delegate.delegate import JobStatus
from stochss_compute.api.delegate.delegate import DelegateConfig

class DaskDelegateConfig(DelegateConfig):
    redis_port = 6379
    redis_address = "0.0.0.0"
    redis_db = 0

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
        self.task_map: dict[str, Future] = { }
        # self.cluster = LocalCluster(
        #     dashboard_address=f"{delegate_config.dask_dashboard_address}:{delegate_config.dask_dashboard_port}",
        #     n_workers=delegate_config.dask_worker_count,
        #     threads_per_worker=delegate_config.dask_worker_threads,
        #     memory_limit=delegate_config.dask_worker_memory_limit
        # )

        # Initialize the Dask client and connect to the specified cluster.
        cluster_address = f"tcp://{delegate_config.dask_cluster_address}:{delegate_config.dask_cluster_port}"
        self.client = Client(cluster_address)

        # Connect to the Redis DB.
        self.redis = Redis(
            host=delegate_config.redis_address,
            port=delegate_config.redis_port,
            db=delegate_config.redis_db
        )

        # These routines are meant to be run on the Dask scheduler for an internal view on running tasks.
        self.scheduler_job_exists = lambda dask_scheduler, id: id in dask_scheduler.tasks
        self.scheduler_job_status = lambda dask_scheduler, id: dask_scheduler.tasks[id].state
        self.scheduler_get_worker_with_job = lambda dask_scheduler, id: dask_scheduler.workers

    def __cache_results(self, future: Future):
        # This function will be fired on the Dask worker after the job is complete.
        # It will save the results in the Redis cache.

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
        if self.job_exists(id) or self.job_complete(id):
            return False
        
        # Create a job and set a callback to cache the results once complete.
        job_future: Future = self.client.submit(work, key=id)
        job_future.add_done_callback(self.__cache_results)
    
        fire_and_forget(job_future)

        return True

    def stop_job(self, id: str) -> bool:
        if not self.job_exists(id):
            return False

        dill.loads(self.redis.get(id)).cancel()
        # self.task_map[id].cancel()

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
        }

        # job_future: Future = dill.loads(self.redis.get(id))
        # job_future = self.task_map[id]
        future_status = self.client.run_on_scheduler(self.scheduler_job_status, id=id)

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

    def job_complete(self, id: str) -> bool:
        return self.redis.get(id) is not None

    def job_exists(self, id: str) -> bool:
        return self.client.run_on_scheduler(self.scheduler_job_exists, id=id)

