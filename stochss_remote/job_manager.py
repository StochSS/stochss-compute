import os
import uuid
import pathlib

from stochss_remote.dep_cache import DepCache
from enum import Enum

class JobStatus(Enum):
    RUNNING = 0
    NOT_STARTED = 1
    PAUSED = 2
    STOPPED = 3
    COMPLETE = 4
    HALTED = 5

class SimulationJob():
    def __init__(self, sim, version):
        self.status = JobStatus.NOT_STARTED
        self.sim = sim
        self.version = version
        self.id = uuid.uuid4()
        self.dir = os.path.join(f"jobs/{self.id}/")

        # Download and install the specified solver into the job's directory.
        pathlib.Path(self.dir).mkdir(parents=True, exist_ok=True)
        DepCache.install(self.dir, self.sim, self.version)

    def start(self, model):
        self.status = JobStatus.RUNNING
        pass

    def signal(self, status):
        self.status = status

    def destroy(self):
        os.rmdir(os.path.join(f"jobs/{self.id}"))
