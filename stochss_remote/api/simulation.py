from pathlib import Path
from enum import Enum
from gillespy2.core.model import Model

from . import celery

class Simulation:
    def __init__(self, type: str, hash: str, model: str, params: str):
        self.type = type
        self.hash = hash
        self.model = model
        self.params = params

        self.dir = Path("./job_cache", hash)
        self.config_file = Path(self.dir, "job.json")
        self.model_file = Path(self.dir, "model.json")
        self.results_file = Path(self.dir, "results.json")

    def run(self):
        if self.type == "gillespy2":
            self._run_gillespy2.apply_async((self.model, self.params), task_id=self.hash)

        return self.hash

    @celery.task()
    def _run_gillespy2(model: str, params: str):
        model = Model.from_json(model)
        results = model.run()
        
        return results.to_json()

    def status(id: str):
        return celery.AsyncResult(id).status

    def result(id: str):
        return celery.AsyncResult(id).get()

class SimulationStatus(Enum):
    NOT_INIT = 0
    INSTALLING = 1
    READY = 2
    RUNNING = 3
    PAUSED = 4
    STOPPED = 5
    COMPLETE = 6
    HALTED = 7