import gillespy2
from gillespy2.core import jsonify

class SimulationRunRequest():
    def __init__(self, model: gillespy2.Model, algorithm: str) -> None:
        self.model = model.to_json()
        self.algorithm = algorithm

        