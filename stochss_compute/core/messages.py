from abc import ABC, abstractmethod
from gillespy2 import Model, Results
from enum import Enum
from tornado.escape import json_encode, json_decode
from hashlib import md5

class SimStatus(Enum):
    PENDING = 'The simulation is pending.'
    RUNNING = 'The simulation is still running.'
    READY = 'Simulation is done and results exist locally.'
    ERROR = 'The Simulation has encountered an error.'
    
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
    def __init__(self, status, message, results = None):
        self.status = status
        self.message = message
        self.results = results
    
    def encode(self):
        if type(self.results) is not str:
            encode_results = Results.from_json(self.results)
        else:
            encode_results = self.results
        return {'status': self.status,
                'message': self.message,
                'results': encode_results}
    
    @classmethod
    def parse(self, raw_response):
        response_dict = json_decode(raw_response)
        status = response_dict['status']
        message = response_dict['message']
        results = Results.from_json(response_dict['results'])
        return SimulationRunResponse(status, message, results)
