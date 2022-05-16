import requests

from enum import Enum

from requests.exceptions import ConnectionError
from time import sleep

from pydantic import BaseModel

class Endpoint(Enum):
    JOB = 1
    RESULT = 2
    GILLESPY2_MODEL = 3
    GILLESPY2_RESULTS = 4

class ComputeServer():
    def __init__(self, host, port: int = 80):
        self.host = host
        self.port = port

        self.address = f"http://{host}:{port}/api/v1"

        self.job_api = f"{self.address}/job"
        self.memory_api = f"{self.address}/memory"
        self.gillespy2_model_api = f"{self.address}/gillespy2/model"
        self.gillespy2_results_api = f"{self.address}/gillespy2/results"

        self.endpoints = {
            Endpoint.JOB: self.job_api,
            Endpoint.RESULT: self.memory_api,
            Endpoint.GILLESPY2_MODEL: self.gillespy2_model_api,
            Endpoint.GILLESPY2_RESULTS: self.gillespy2_results_api
        }

    def get(self, endpoint: Endpoint, sub: str) -> requests.Response:
        url = f"{self.endpoints[endpoint]}{sub}"
        print(f"[GET] {url}")
        return requests.get(f"{self.endpoints[endpoint]}{sub}")

    def post(self, endpoint: Endpoint, sub: str, request: BaseModel = None) -> requests.Response:
        url = f"{self.endpoints[endpoint]}{sub}"
        retry = 1
        sec = 3
        while retry <= 3:
            try:
                if request is None:
                    print(f"[POST] {url}")
                    return requests.post(url)
                print(f"[{type(request).__name__}] {url}")
                return requests.post(url, json=request.json())

            except ConnectionError as ce:
                print(f"Connection refused by server. Retrying in {sec} seconds....")
                sleep(sec)
                retry += 1
                sec *= retry
            
            except Exception as e:
                print(f"Unknown error: {e}. Retrying in {sec} seconds....")
                sleep(sec)
                retry += 1
                sec *= retry

