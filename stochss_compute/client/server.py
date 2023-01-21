'''
Server(ABC)
'''
from time import sleep
from abc import ABC, abstractmethod
import requests
from stochss_compute.client.endpoint import Endpoint
from stochss_compute.core.messages import Request

class Server(ABC):
    '''
    Server parent class with hard coded endpoints.
    '''

    _endpoints = {
        Endpoint.SIMULATION_GILLESPY2: "/api/v2/simulation/gillespy2",
        Endpoint.CLOUD: "/api/v2/cloud"
    }

    def __init__(self) -> None:
        raise TypeError('Server cannot be instantiated directly. Must be ComputeServer or Cluster.')

    @property
    @abstractmethod
    def address(self):
        '''
        NotImplemented
        '''
        return NotImplemented

    def get(self, endpoint, sub):
        '''
        Send a GET request to endpoint.
        '''
        url = f"{self.address}{self._endpoints[endpoint]}{sub}"
        n_try = 1
        sec = 3
        while n_try <= 3:
            try:
                return requests.get(url, timeout=30)

            except ConnectionError:
                print(f"Connection refused by server. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try
            except Exception as err:
                print(f"Unknown error: {err}. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try

    def post(self, endpoint: Endpoint, sub: str, request: Request = None):
        '''
        Send a POST request to endpoint.
        '''

        if self.address is NotImplemented:
            raise NotImplementedError

        url = f"{self.address}{self._endpoints[endpoint]}{sub}"
        n_try = 1
        sec = 3
        while n_try <= 3:
            try:
                if request is None:
                    print(f"[POST] {url}")
                    return requests.post(url, timeout=30)
                print(f"[{type(request).__name__}] {url}")
                return requests.post(url, json=request.encode(), timeout=30)

            except ConnectionError:
                print(f"Connection refused by server. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try
            except Exception as err:
                print(f"Unknown error: {err}. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try
