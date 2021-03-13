from enum import Enum

class JobStatus(Enum):
    RUNNING
    NOT_STARTED
    PAUSED
    STOPPED
    COMPLETE
    HALTED

class SimulationJob():
    def __init__(self, sim, version, model):
        self.status = JobStatus.NOT_STARTED
        self.sim = sim
        self.version = version
        self.model

    def start(self):
        self.status = JobStatus.RUNNING
        pass

    def signal(self, status):
        self.status = status
