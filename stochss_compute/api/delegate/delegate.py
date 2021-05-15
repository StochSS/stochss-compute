from enum import Enum
from abc import ABC, abstractmethod

from pkg_resources import WorkingSet

class Status(Enum):
    WAITING = 0
    RUNNING = 1
    STOPPED = 2
    FAILED = 3
    DONE = 4

class JobStatus:
    status_id: Status = 0
    status_text: str = ""
    is_done: bool = False
    has_failed: bool = False

class Delegate(ABC):
    type: str = ""

    @abstractmethod
    def __init__(self, **kwargs):
        """
        Instantiate a new delegate instance.
        """
        pass

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the compute instance.

        :returns: True if successful, False if not.
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the delegate's connection to a compute instance.
        """
        pass

    @abstractmethod
    def create_job(self, id: str) -> bool:
        """
        Create a new job with the specified ID.

        :returns: True if successful, False if not.
        """
        pass

    @abstractmethod
    def start_job(self, id: str, work: function, *args, **kwargs) -> bool:
        """
        Start a job with the specified ID.

        :returns: True if successful, False if not.
        """
        pass

    @abstractmethod
    def stop_job(self, id: str) -> bool:
        """
        Stop a job with the specified ID.

        :returns: True if successful, False if not.
        """
        pass

    @abstractmethod
    def job_status(self, id: str) -> JobStatus:
        """
        Get the status of a job with the specified ID.

        :returns: A JobStatus instance with status details.
        """
        pass

    @abstractmethod
    def job_results(self, id: str) -> str:
        """
        The raw results of a job with the specified ID.

        :returns: The results object of the work done.
        """
        pass

    @abstractmethod
    def job_exists(self, id: str) -> bool:
        """
        Check if a job with the specified ID exists in the delegate.

        :returns: True if the job exists, False if it does not.
        """
        pass

