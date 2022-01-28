from __future__ import annotations

from enum import IntEnum
from abc import ABC, abstractmethod
from typing import Callable

class JobState(IntEnum):
    WAITING = 0
    RUNNING = 1
    STOPPED = 2
    FAILED = 3
    DONE = 4
    DOES_NOT_EXIST = 5

class JobStatus:
    status_id: JobState = 0
    status_text: str = ""
    is_done: bool = False
    has_failed: bool = False

class DelegateConfig(ABC):
    def __init__(self, **kwargs):
        """
        Easy way to apply some number of named arguments onto self.
        """

        self.__dict__ = {**self.__dict__, **kwargs}

class Delegate(ABC):
    type: str = ""

    @abstractmethod
    def __init__(self, delegate_config: DelegateConfig):
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
    def create_job(self, job_id: str) -> bool:
        """
        Create a new job with the specified ID.

        :returns: True if successful, False if not.
        """
        pass

    @abstractmethod
    def start_job(self, job_id: str, work: Callable, *args, **kwargs) -> bool:
        """
        Start a job with the specified ID.

        :returns: True if successful, False if not.
        """
        pass

    @abstractmethod
    def stop_job(self, job_id: str) -> bool:
        """
        Stop a job with the specified ID.

        :returns: True if successful, False if not.
        """
        pass

    @abstractmethod
    def job_status(self, job_id: str) -> JobStatus:
        """
        Get the status of a job with the specified ID.

        :returns: A JobStatus instance with status details.
        """
        pass

    @abstractmethod
    def job_results(self, job_id: str) -> str:
        """
        The raw results of a job with the specified ID.

        :returns: The results object of the work done.
        """
        pass

    @abstractmethod
    def job_exists(self, job_id: str) -> bool:
        """
        Check if a job with the specified ID exists in the delegate.

        :returns: True if the job exists, False if it does not.
        """
        pass

    @abstractmethod
    def job_complete(self, job_id: str) -> bool:
        """
        Check if a job with the specified ID is complete.

        :returns: True if the job is complete, False if it is not.
        """
        pass

