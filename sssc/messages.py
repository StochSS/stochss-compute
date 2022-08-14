from gillespy2.core import Model, Results
from enum import Enum
from tornado.escape import json_encode

class SimStatus(Enum):
    PENDING = 'The simulation is pending.'
    RUNNING = 'The simulation is still running.'
    READY = 'Simulation is done and results exist locally.'
    ERROR = 'The Simulation has encountered an error.'
    
class Request:
    pass

class Response:
    pass

class SimulationRunRequest(Request):
    def __init__(self, model: Model, **params):
        self._model = model.to_json()
        self.kwargs = json_encode(params)

    @property
    def model(self):
        return Model.from_json(self._model)

class SimulationRunResponse(Response):
    def __init__(self, status: SimStatus, message: str = None, results: Results = None):
        self.status = status
        self.message = message
        if results is not None:
            self._results = results.to_json()
    
    @property
    def results(self):
        if self._results is None:
            return self._results
        else:
            return Results.from_json(self._results)
