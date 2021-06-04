from pathlib import Path
from stochss_compute.api.delegate.delegate import JobStatus
from gillespy2.core.model import Model

from . import delegate

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
        # If the job already exists, do nothing.
        if delegate.job_exists(self.hash) and delegate.job_status(self.hash).is_done:
            return self.hash

        # Create a new job with the specified ID.
        if not delegate.create_job(self.hash):
            raise Exception(f"Failed to create job with ID: {id} on delegate type: {delegate.type}.")

        # Test the delegate's connection.
        if not delegate.test_connection():
            raise Exception(f"Failed to connect to compute instance with delegate type: {delegate.type}.")

        if self.type == "gillespy2":
            delegate.start_job(self.hash, self._run_gillespy2, (self.model, self.params))

        return self.hash

    def _run_gillespy2(model: str, params: str):
        model = Model.from_json(model)
        results = model.run()
        
        return results.to_json()

    def status(id: str) -> JobStatus:
        if not delegate.job_exists(id):
            return None

        return delegate.job_status(id)

    def result(id: str):
        if not delegate.job_exists(id):
            return None

        return delegate.job_results(id)