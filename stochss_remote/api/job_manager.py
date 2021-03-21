import os, uuid, pathlib
from enum import Enum

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
        self.jobs[sim.id] = sim

    def start(self, id, **params):
        self.jobs[id].status = JobStatus.RUNNING
        self.jobs[id].model.run(params)

    def get(self, id):
        return self.jobs[id]
