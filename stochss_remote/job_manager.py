import os
import uuid
import pathlib

from stochss_remote.sim_cache import SimCache
from enum import Enum

jobs = {}

class JobStatus(Enum):
    NOT_INIT = 0
    INSTALLING = 1
    READY = 2
    RUNNING = 3
    PAUSED = 4
    STOPPED = 5
    COMPLETE = 6
    HALTED = 7

class SimulationJob():
    def __init__(self, sim, version):
        self.status = JobStatus.NOT_INIT
        self.sim = sim
        self.version = version
        self.id = str(uuid.uuid4())
        self.dir = os.path.join(f"jobs/{self.id}/")

        jobs[self.id] = self

def install(id):
    jobs[id].status = JobStatus.INSTALLING

    # Download and install the specified solver into the job's directory.
    pathlib.Path(jobs[id].dir).mkdir(parents=True, exist_ok=True)
    SimCache.install(jobs[id].dir, jobs[id].sim, jobs[id].version)

    jobs[id].status = JobStatus.READY

def start(self, model):
    self.status = JobStatus.RUNNING
    pass

def signal(self, status):
    self.status = status

def destroy(self):
    os.rmdir(os.path.join(f"jobs/{self.id}"))
