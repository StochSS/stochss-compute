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
