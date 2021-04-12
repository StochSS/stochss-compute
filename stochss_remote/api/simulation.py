import uuid, os, dill
from gillespy2 import Model

import stochss_remote.api.request_helpers
from stochss_remote.api.job_manager import JobStatus

class Simulation():
    def __init__(self, sim, version):
        self.status = JobStatus.READY
        self.sim = sim
        self.version = version
        self.id = str(uuid.uuid4())
        self.dir = os.path.join(f"jobs/{self.id}/")

    def start(self, model_json):
        return self.__start_gillespy2(model_json)

    def __start_gillespy2(self, model_json):
        # Convert the pickled model into an executable object.
        model_dict = request_helpers.from_pickle(model_json)
        model = gillespy2.Model(name = "Test")

        model.__dict__ = model_dict
        return model.run()
        