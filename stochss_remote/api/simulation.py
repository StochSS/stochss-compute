import uuid
from stochss_remote.api.job_manager import JobStatus

class Simulation():
    def __init__(self, sim, version):
        self.status = JobStatus.READY
        self.sim = sim
        self.version = version
        self.id = str(uuid.uuid4())
        self.dir = os.path.join(f"jobs/{self.id}/")

    def start(self, model_json):
        self.__start_gillespy2(model)

    def __start_gillespy2(self, model_json):
        import json
        import gillespy2

        from types import SimpleNamespace

        # Convert the jsonified model into a namespaced object.
        model_obj = json.load(model_json, object_hook = lambda d: SimpleNamespace(**d))
        model = gillespy.Model.__init__(self, name = "Temp")

        model.__dict__ = model_obj.__dict__
        