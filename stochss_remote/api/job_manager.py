import os
import uuid
import pathlib

from stochss_remote.api.sim_cache import SimCache
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


class JobManager():
    jobs = { }

    def add(self, sim):
        jobs[sim.id] = sim

    def start(self, id):
        jobs[id].status = JobStatus.RUNNING

    def get(self, id):
        return jobs[id]
