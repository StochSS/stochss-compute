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
    @staticmethod
    @abstractmethod
    def parse(raw_request):
        pass

class Response(ABC):
    @abstractmethod
    def encode(self):
        pass
    @staticmethod
    @abstractmethod
    def parse(raw_response):
        pass


class SimulationRunRequest(Request):
    def __init__(self, model, **params):
        self.model = model
        self.kwargs = params

    def encode(self):
        return {'model': self.model.to_json(),
                'kwargs': json_encode(self.kwargs)}

    @staticmethod
    def parse(raw_request):
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
    def __init__(self, status, error_message = None, results_id = None, results = None):
        self.status = status
        self.error_message = error_message
        self.results_id = results_id
        self.results = results
    
    def encode(self):
        if self.results is None:
            encode_results = self.results
        else:
            encode_results = self.results.to_json()
        return {'status': self.status.name,
                'error_message': self.error_message or '',
                'results_id': self.results_id or '',
                'results': encode_results or ''}
    
    @staticmethod
    def parse(raw_response):
        response_dict = json_decode(raw_response)
        status = SimStatus.from_str(response_dict['status'])
        results_id = response_dict['results_id']
        error_message = response_dict['error_message']
        if response_dict['results'] != '':
            results = Results.from_json(response_dict['results'])
        else:
            results = None
        return SimulationRunResponse(status, error_message, results_id, results)

class StatusRequest(Request):
    def __init__(self, results_id):
        self.results_id = results_id
    def encode(self):
        return self.__dict__
    @staticmethod
    def parse(raw_request):
        request_dict = json_decode(raw_request)
        return StatusRequest(request_dict['results_id'])

class StatusResponse(Response):
    def __init__(self, status, error_message = ''):
        self.status = status
        self.error_message = error_message
    
    def encode(self):
        return {'status': self.status.name,
                'error_message': self.error_message}
    
    @staticmethod
    def parse(raw_response):
        response_dict = json_decode(raw_response)
        status = SimStatus.from_str(response_dict['status'])
        return StatusResponse(status, response_dict['error_message'])

class ResultsRequest(Request):
    def __init__(self, results_id):
        self.results_id = results_id
    def encode(self):
        return self.__dict__
    @staticmethod
    def parse(raw_request):
        request_dict = json_decode(raw_request)
        return ResultsRequest(request_dict['results_id'])

class ResultsResponse(Response):
    def __init__(self, results = None):
        self.results = results
    
    def encode(self):
        if self.results is None:
            encode_results = self.results
        else:
            encode_results = self.results.to_json()
        return {'results': encode_results or ''}
    
    @staticmethod
    def parse(raw_response):
        response_dict = json_decode(raw_response)
        if response_dict['results'] != '':
            results = Results.from_json(response_dict['results'])
        else:
            results = None
        return ResultsResponse(results)