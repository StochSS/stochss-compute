import requests

from enum import Enum

from urllib.parse import urljoin
from urllib.parse import urlparse

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
        print(f"{self.endpoints[endpoint]}{sub}")
        return requests.get(f"{self.endpoints[endpoint]}{sub}")

    def post(self, endpoint: Endpoint, sub: str, request: BaseModel = None) -> requests.Response:
        url = f"{self.endpoints[endpoint]}{sub}"
        print(url)

        if request is None:
            return requests.post(url)

        return requests.post(url, json=request.json())

