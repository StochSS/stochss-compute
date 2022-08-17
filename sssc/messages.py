from urllib import request
from gillespy2.core import Model, Results
from enum import Enum
from tornado.escape import json_encode, json_decode

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
        self._model = model
        self._kwargs = params

    @property
    def model(self):
        return Model.from_json(self._model)

    @property
    def kwargs(self):
        return json_decode(self._kwargs)

    def encode(self):
        return {'model': self._model.to_json(), 'kwargs': json_encode(self._kwargs)}

    @classmethod
    def parse(self, raw_request: str):
        request_dict = json_decode(raw_request)
        kwargs_dict = json_decode(request_dict['model'])
        kwargs_dict = json_decode(request_dict['kwargs'])
        return SimulationRunRequest(, **kwargs_dict)

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
