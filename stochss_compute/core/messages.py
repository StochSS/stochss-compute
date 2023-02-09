'''
stochss_compute.core.messages
'''
# StochSS-Compute is a tool for running and caching GillesPy2 simulations remotely.
# Copyright (C) 2019-2023 GillesPy2 and StochSS developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
    Base class.
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
    Base class.
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
    A simulation request.

    :param model: A model to run.
    :type model: gillespy2.Model

    :param kwargs: kwargs for the model.run() call.
    :type kwargs: dict[str, Any]
    '''
    def __init__(self, model, **kwargs):
        self.model = model
        self.kwargs = kwargs

    def encode(self):
        '''
        JSON-encode model and then encode self to dict.
        '''
        return {'model': self.model.to_json(),
                'kwargs': self.kwargs}

    @staticmethod
    def parse(raw_request):
        '''
        Parse HTTP request.

        :param raw_request: The request.
        :type raw_request: dict[str, str]

        :returns: The decoded object.
        :rtype: SimulationRunRequest
        '''
        request_dict = json_decode(raw_request)
        model = Model.from_json(request_dict['model'])
        kwargs = request_dict['kwargs']
        return SimulationRunRequest(model, **kwargs)

    def hash(self):
        '''
        Generate a unique hash of this simulation request.
        Does not include number_of_trajectories in this calculation.

        :returns: md5 hex digest.
        :rtype: str
        '''
        anon_model_string = self.model.to_anon().to_json(encode_private=False)
        popped_kwargs = {kw:self.kwargs[kw] for kw in self.kwargs if kw!='number_of_trajectories'}
        kwargs_string = json_encode(popped_kwargs)
        request_string =  f'{anon_model_string}{kwargs_string}'
        _hash = md5(str.encode(request_string)).hexdigest()
        return _hash

class SimulationRunResponse(Response):
    '''
    A response from the server regarding a SimulationRunRequest.
    
    :param status: The status of the simulation.
    :type status: SimStatus

    :param error_message: Possible error message.
    :type error_message: str | None

    :param results_id: Hash of the simulation request. Identifies the results.
    :type results_id: str | None

    :param results: JSON-Encoded gillespy2.Results
    :type results: str | None
    '''
    def __init__(self, status, error_message = None, results_id = None, results = None, task_id = None):
        self.status = status
        self.error_message = error_message
        self.results_id = results_id
        self.results = results
        self.task_id = task_id

    def encode(self):
        '''
       Encode self to dict.
        '''
        return {'status': self.status.name,
                'error_message': self.error_message or '',
                'results_id': self.results_id or '',
                'results': self.results or '',
                'task_id': self.task_id or '',}

    @staticmethod
    def parse(raw_response):
        '''
        Parse HTTP response.

        :param raw_response: The response.
        :type raw_response: dict[str, str]

        :returns: The decoded object.
        :rtype: SimulationRunResponse
        '''
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
    A request for simulation status.

    :param results_id: Hash of the SimulationRunRequest
    :type results_id: str
    '''
    def __init__(self, results_id):
        self.results_id = results_id
    def encode(self):
        '''
        :returns: self.__dict__
        :rtype: dict
        '''
        return self.__dict__

    @staticmethod
    def parse(raw_request):
        '''
        Parse HTTP request.

        :param raw_request: The request.
        :type raw_request: dict[str, str]

        :returns: The decoded object.
        :rtype: StatusRequest
        '''
        request_dict = json_decode(raw_request)
        return StatusRequest(request_dict['results_id'])

class StatusResponse(Response):
    '''
    A response from the server about simulation status.

    :param status: Status of the simulation
    :type status: SimStatus
    
    :param message: Possible error message or otherwise
    :type message: str
    '''
    def __init__(self, status, message = None):
        self.status = status
        self.message = message

    def encode(self):
        '''
        Encodes self.
        :returns: self as dict
        :rtype: dict[str, str]
        '''
        return {'status': self.status.name,
                'message': self.message or ''}

    @staticmethod
    def parse(raw_response):
        '''
        Parse HTTP response.

        :param raw_response: The response.
        :type raw_response: dict[str, str]

        :returns: The decoded object.
        :rtype: StatusResponse
        '''
        response_dict = json_decode(raw_response)
        status = SimStatus.from_str(response_dict['status'])
        message = response_dict['message']
        if not message:
            return StatusResponse(status)
        else:
            return StatusResponse(status, message)

class ResultsRequest(Request):
    '''
    Request results from the server.

    :param results_id: Hash of the SimulationRunRequest
    :type results_id: str
    '''
    def __init__(self, results_id):
        self.results_id = results_id
    def encode(self):
        '''
        :returns: self.__dict__
        :rtype: dict
        '''
        return self.__dict__
    @staticmethod
    def parse(raw_request):
        '''
        Parse HTTP request.

        :param raw_request: The request.
        :type raw_request: dict[str, str]

        :returns: The decoded object.
        :rtype: ResultsRequest
        '''
        request_dict = json_decode(raw_request)
        return ResultsRequest(request_dict['results_id'])

class ResultsResponse(Response):
    '''
    A response from the server about the Results.

    :param results: The requested Results from the cache. (JSON)
    :type results: str
    
    '''
    def __init__(self, results = None):
        self.results = results

    def encode(self):
        '''
        :returns: self.__dict__
        :rtype: dict
        '''
        return {'results': self.results or ''}

    @staticmethod
    def parse(raw_response):
        '''
        Parse HTTP response.

        :param raw_response: The response.
        :type raw_response: dict[str, str]

        :returns: The decoded object.
        :rtype: ResultsResponse
        '''
        response_dict = json_decode(raw_response)
        if response_dict['results'] != '':
            results = Results.from_json(response_dict['results'])
        else:
            results = None
        return ResultsResponse(results)

class SourceIpRequest(Request):
    '''
    Restrict server access.

    :param cloud_key: Random key generated locally during launch.
    :type cloud_key: str
    '''
    def __init__(self, cloud_key):
        self.cloud_key = cloud_key
    def encode(self):
        '''
        :returns: self.__dict__
        :rtype: dict
        '''
        return self.__dict__
    @staticmethod
    def parse(raw_request):
        '''
        Parse HTTP request.

        :param raw_request: The request.
        :type raw_request: dict[str, str]

        :returns: The decoded object.
        :rtype: SourceIpRequest
        '''
        request_dict = json_decode(raw_request)
        return SourceIpRequest(request_dict['cloud_key'])

class SourceIpResponse(Response):
    '''
    Response from server containing IP address of the source.

    :param source_ip: IP address of the client.
    :type source_ip: str
    '''
    def __init__(self, source_ip):
        self.source_ip = source_ip

    def encode(self):
        '''
        :returns: self.__dict__
        :rtype: dict
        '''
        return self.__dict__

    @staticmethod
    def parse(raw_response):
        '''
        Parses a http response and returns a python object.

        :param raw_response: A raw http SourceIpResponse from the server.
        :type raw_response: str

        :returns: The decoded object.
        :rtype: SourceIpResponse
        '''
        response_dict = json_decode(raw_response)
        return SourceIpResponse(response_dict['source_ip'])
