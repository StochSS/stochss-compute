
from abc import ABC, abstractmethod
import requests

from stochss_compute.client.endpoint import Endpoint
from stochss_compute.core.messages import Request

from requests.exceptions import ConnectionError
from time import sleep



class Server(ABC):    

    _endpoints = {
        Endpoint.SIMULATION_GILLESPY2: "/api/v2/simulation/gillespy2",
        Endpoint.CLOUD: "/api/v2/cloud"
    }

    def __init__(self) -> None:
        raise TypeError('Server cannot be instantiated directly. Must be ComputeServer or Cluster.')

    @property
    @abstractmethod
    def address(self):
        return NotImplemented

    def _get(self, endpoint, sub):
        url = f"{self.address}{self._endpoints[endpoint]}{sub}"
        print(f"[GET] {url}")
        n_try = 1
        sec = 3
        while n_try <= 3:
            try:
                return requests.get(url)

            except ConnectionError as ce:
                print(f"Connection refused by server. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try
            
            except Exception as e:
                print(f"Unknown error: {e}. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try

    def _post(self, endpoint: Endpoint, sub: str, request: Request = None):

        if self.address is NotImplemented:
            raise NotImplementedError

        url = f"{self.address}{self._endpoints[endpoint]}{sub}"
        n_try = 1
        sec = 3
        while n_try <= 3:
            try:
                if request is None:
                    print(f"[POST] {url}")
                    return requests.post(url)
                print(f"[{type(request).__name__}] {url}")
                return requests.post(url, json=request._encode())

            except ConnectionError as ce:
                print(f"Connection refused by server. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try
            
            except Exception as e:
                print(f"Unknown error: {e}. Retrying in {sec} seconds....")
                sleep(sec)
                n_try += 1
                sec *= n_try

