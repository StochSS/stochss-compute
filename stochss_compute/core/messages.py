'''
stochss_compute.core.messages
'''
from abc import ABC, abstractmethod
from enum import Enum
from hashlib import md5
from gillespy2 import Model, Results
from tornado.escape import json_encode, json_decode


class SimStatus(Enum):
    '''
    Status describing a remote simulation.
    '''
    PENDING = 'The simulation is pending.'
    RUNNING = 'The simulation is still running.'
    READY = 'Simulation is done and results exist in the cache.'
    ERROR = 'The Simulation has encountered an error.'
    DOES_NOT_EXIST = 'There is no evidence of this simulation either running or on disk.'

    @staticmethod
    def from_str(name):
        '''
        Convert str to Enum.
        '''
        if name == 'PENDING':
            return SimStatus.PENDING
        if name == 'RUNNING':
            return SimStatus.RUNNING
        if name == 'READY':
            return SimStatus.READY
        if name == 'ERROR':
            return SimStatus.ERROR
        if name == 'DOES_NOT_EXIST':
            return SimStatus.DOES_NOT_EXIST

class Request(ABC):
    '''
    Talk about class.
    '''
    @abstractmethod
    def encode(self):
        '''
        Encode self for http.
        '''
    @staticmethod
    @abstractmethod
    def parse(raw_request):
        '''
        Parse http for python.
        '''

class Response(ABC):
    '''
    Response abstracted down to the essentials.
    '''
    @abstractmethod
    def encode(self):
        '''
        Encode self for http.
        '''
    @staticmethod
    @abstractmethod
    def parse(raw_response):
        '''
        Parse http for python.
        '''


class SimulationRunRequest(Request):
    '''
    :type model: gillespy2.Model
    '''
    def __init__(self, model, **kwargs):
        self.model = model
        self.kwargs = kwargs

    def encode(self):
        return {'model': self.model.to_json(),
                'kwargs': self.kwargs}

    @staticmethod
    def parse(raw_request):
        request_dict = json_decode(raw_request)
        model = Model.from_json(request_dict['model'])
        kwargs = request_dict['kwargs']
        return SimulationRunRequest(model, **kwargs)

    def hash(self):
        '''
        '''
        anon_model_string = self.model.to_anon().to_json(encode_private=False)
        popped_kwargs = {kw:self.kwargs[kw] for kw in self.kwargs if kw!='number_of_trajectories'}
        kwargs_string = json_encode(popped_kwargs)
        request_string =  f'{anon_model_string}{kwargs_string}'
        _hash = md5(str.encode(request_string)).hexdigest()
        return _hash

class SimulationRunResponse(Response):
    '''
    :type status: SimStatus
    :type error_message: str | None
    :type results_id: str | None
    :type results: str | None
    '''
    def __init__(self, status, error_message = None, results_id = None, results = None, task_id = None):
        self.status = status
        self.error_message = error_message
        self.results_id = results_id
        self.results = results
        self.task_id = task_id
    
    def encode(self):
        return {'status': self.status.name,
                'error_message': self.error_message or '',
                'results_id': self.results_id or '',
                'results': self.results or '',
                'task_id': self.task_id or '',}
    
    @staticmethod
    def parse(raw_response):
        response_dict = json_decode(raw_response)
        status = SimStatus.from_str(response_dict['status'])
        results_id = response_dict['results_id']
        error_message = response_dict['error_message']
        task_id = response_dict['task_id']
        if response_dict['results'] != '':
            results = Results.from_json(response_dict['results'])
        else:
            results = None
        return SimulationRunResponse(status, error_message, results_id, results, task_id)

class StatusRequest(Request):
    '''
    :type results_id: str
    '''
    def __init__(self, results_id):
        self.results_id = results_id
    def encode(self):
        return self.__dict__
    @staticmethod
    def parse(raw_request):
        request_dict = json_decode(raw_request)
        return StatusRequest(request_dict['results_id'])

class StatusResponse(Response):
    '''
    :type status: SimStatus
    :type error_message: str
    '''
    def __init__(self, status, message = None):
        self.status = status
        self.message = message
    
    def encode(self):
        return {'status': self.status.name,
                'message': self.message or ''}
    
    @staticmethod
    def parse(raw_response):
        response_dict = json_decode(raw_response)
        status = SimStatus.from_str(response_dict['status'])
        message = response_dict['message']
        if not message:
            return StatusResponse(status)
        else:
            return StatusResponse(status, message)
            
class ResultsRequest(Request):
    '''
    :type results_id: str
    '''
    def __init__(self, results_id):
        self.results_id = results_id
    def encode(self):
        return self.__dict__
    @staticmethod
    def parse(raw_request):
        request_dict = json_decode(raw_request)
        return ResultsRequest(request_dict['results_id'])

class ResultsResponse(Response):
    '''
    :type results: str | None
    '''
    def __init__(self, results = None):
        self.results = results
    
    def encode(self):
        return {'results': self.results or ''}
    
    @staticmethod
    def parse(raw_response):
        response_dict = json_decode(raw_response)
        if response_dict['results'] != '':
            results = Results.from_json(response_dict['results'])
        else:
            results = None
        return ResultsResponse(results)

class SourceIpRequest(Request):
    '''
    :type cloud_key: str
    '''
    def __init__(self, cloud_key):
        self.cloud_key = cloud_key
    def encode(self):
        return self.__dict__
    @staticmethod
    def parse(raw_request):
        request_dict = json_decode(raw_request)
        return SourceIpRequest(request_dict['cloud_key'])

class SourceIpResponse(Response):
    '''
    Response from server containing IP address of the source.
    '''
    def __init__(self, source_ip):
        self.source_ip = source_ip

    def encode(self):
        return self.__dict__

    @staticmethod
    def parse(raw_response):
        '''
        Parses a http response and returns a python object.

        :param raw_response: A raw http SourceIpResponse from the server.
        '''
        response_dict = json_decode(raw_response)
        return SourceIpResponse(response_dict['source_ip'])
