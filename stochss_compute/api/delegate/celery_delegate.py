from celery import Celery
from .delegate import Delegate, JobStatus, Status

class CeleryDelegate(Delegate):
    type = "celery"

    def __init__(self, **kwargs):
        required_keys = [
            "celery_name",
            "celery_config"
        ]

        # Validate the input args.
        for key in required_keys:
            if key not in kwargs:
                raise Exception(f"Required key: {key} not found in kwargs.")

            if kwargs[key] is None:
                raise Exception(f"Value at required key: {key} is None.")

        self.celery = Celery(kwargs["name"])
        self.celery.config_from_object(kwargs["celery_config"])

    def connect(self) -> bool:
        # Celery doesn't have a concept of 'connect then start', so we're going to shim this for now.
        return True

    def test_connection(self) -> bool:
        return self.celery.control.ping() is not None

    def create_job(self, id: str) -> bool:
        # Celery doesn't have a job create -> runon job workflow, so we're just going to check to see if the job exists.
        return not self.job_exists(id)

    def start_job(self, id: str, work: function, *args, **kwargs) -> bool:
        if not self.job_exists(id):
            raise Exception("A job with ID: {id} does not exist.")

        # The incoming function should NOT be decorated, so we need to do it manually to support celery.apply_async()
        work = self.celery.task(work)
        work.apply_async((args, kwargs), task_id=id)

    def job_status(self, id: str) -> JobStatus:
        if not self.job_exists(id):
            raise Exception("A job with ID: {id} does not exist.")

        # Use a celery -> JobStatus mapping to fit the delegate specification.
        celery_status = self.celery.AsyncResult(id).status
        status_mapping = {
            "PENDING": (Status.WAITING, "The job exists but hasn't been started yet."),
            "STARTED": (Status.RUNNING, "The job is currently running."),
            "RETRY": (Status.RUNNING, "The job is currently running."),
            "FAILURE": (Status.FAILED, "The job has failed."),
            "SUCCESS": (Status.DONE, "The job is complete.")
        }

        status = JobStatus()
        status.status_id = status_mapping[celery_status][0]
        status.status_text = status_mapping[celery_status][1]

        status.is_done = status.status_id is Status.DONE
        status.has_failed = status.status_id is Status.FAILED

        return status

    def job_results(self, id: str):
        # If the job is not done do nothing.
        if not self.job_status(id).is_done:
            return None

        # Otherwise, return the results of the job.
        return self.celery.AsyncResult(id).get()

    def job_exists(self, id: str) -> bool:
        # If the job does not exist then the status will always be 'PENDING'.
        return self.celery.AsyncResult(id).status is not "PENDING"