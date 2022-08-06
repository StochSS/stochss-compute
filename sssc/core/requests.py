from mimetypes import init
import gillespy2
import json
class SimulationRunRequest:
    def __init__(self, model: gillespy2.Model, algorithm: str) -> None:
        self.model = model.to_json()
        self.algorithm = algorithm
    def json(self):
        return json.dumps(self.__dict__)
