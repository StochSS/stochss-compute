from abc import ABC, abstractmethod
from gillespy2 import Model, Results
from enum import Enum
from tornado.escape import json_encode, json_decode
from hashlib import md5

from stochss_compute.core.remote_results import RemoteResults

class SimStatus(Enum):
    PENDING = 'The simulation is pending.'
    RUNNING = 'The simulation is still running.'
    READY = 'Simulation is done and results exist locally.'
    ERROR = 'The Simulation has encountered an error.'

    @staticmethod
    def from_str(name):
        if name == 'PENDING':
            return SimStatus.PENDING
        if name == 'RUNNING':
            return SimStatus.RUNNING
        if name == 'READY':
            return SimStatus.READY
        if name == 'ERROR':
            return SimStatus.ERROR
    
class Request(ABC):
    @abstractmethod
    def encode(self):
        pass
    @classmethod
    @abstractmethod
    def parse(self, raw_request):
        pass

class Response:
    pass

class SimulationRunRequest(Request):
    def __init__(self, model, **params):
        self.model = model
        self.kwargs = params

    def encode(self):
        return {'model': self.model.to_json(),
                'kwargs': json_encode(self.kwargs)}

    @classmethod
    def parse(self, raw_request):
        request_dict = json_decode(raw_request)
        model = Model.from_json(request_dict['model'])
        kwargs_dict = json_decode(request_dict['kwargs'])
        return SimulationRunRequest(model, **kwargs_dict)

    def hash(self):
        anon_model_string = self.model.to_anon().to_json(encode_private=False)
        kwargs_string = json_encode(self.kwargs)
        request_string =  f'{anon_model_string}{kwargs_string}'
        return md5(str.encode(request_string)).hexdigest()

class SimulationRunResponse(Response):
    def __init__(self, status, message = "", results_id = "", results = ""):
        self.status = status
        self.message = message
        self.results_id = results_id
        self.results = results
    
    def encode(self):
        if isinstance(self.results, Results):
            encode_results = Results.from_json(self.results)
        else:
            encode_results = self.results
        return {'status': self.status.name,
                'message': self.message,
                'results_id': self.results_id,
                'results': encode_results}
    
    @classmethod
    def parse(self, raw_response):
        response_dict = json_decode(raw_response)
        status = SimStatus.from_str(response_dict['status'])
        results_id = response_dict['results_id']
        if status == SimStatus.ERROR:
            message = response_dict['message']
        else:
            message = ""
        if status == SimStatus.READY:
            results = Results.from_json(response_dict['results'])
        else:
            results = ""
        return SimulationRunResponse(status, message, results_id, results)
