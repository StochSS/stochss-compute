import os
from enum import Enum
from uuid import uuid5

class JobStatus(Enum):
    RUNNING
    NOT_STARTED
    PAUSED
    STOPPED
    COMPLETE
    HALTED

class Simulation():
    def __init__(self, sim, version):
        self.status = JobStatus.NOT_STARTED
        self.sim = sim
        self.version = version
        self.model = model
        self.id = uuid5()

        os.mkdir(os.path.join(f"jobs/{self.id}/"))

    def start(self, model):
        self.status = JobStatus.RUNNING
        pass

    def signal(self, status):
        self.status = status

    def destroy(self):
        os.rmdir(os.path.join(f"jobs/{self.id}"))
