
import requests

from enum import Enum

from requests.exceptions import ConnectionError
from time import sleep

class Endpoint(Enum):
    GILLESPY2_MODEL = 1
    GILLESPY2_RESULTS = 2
    CLOUD = 3

class SSSCServer:    
    def __init__(self, host, port: int = 29681):
        self.host = host
        self.port = port

        self.address = f"http://{host}:{port}/api/v2"

        self.gillespy2_simulation_api = "/simulation/gillespy2/run"
        self.gillespy2_results_api = "/simulation/gillespy2/results"
        self.cloud_api = "/cloud"

        self.endpoints = {
            Endpoint.GILLESPY2_MODEL: self.gillespy2_simulation_api,
            Endpoint.GILLESPY2_RESULTS: self.gillespy2_results_api,
            Endpoint.CLOUD: self.cloud_api
        }


    def post(self, endpoint: Endpoint, sub: str, request = None) -> requests.Response:

        url = f"{self.address}{self.endpoints[endpoint]}{sub}"

        print(f"[{type(request).__name__}] {url}")
        n_try = 1
        sec = 3
        while n_try <= 3:
            try:
                if request is None:
                    print(f"[POST] {url}")
                    return requests.post(url)
                return requests.post(url, json=request.__dict__)

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

