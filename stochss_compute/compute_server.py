import requests

from enum import Enum

from urllib.parse import urljoin
from urllib.parse import urlparse

from pydantic import BaseModel

class Endpoint(Enum):
    JOB = 1
    RESULT = 2

class ComputeServer():
    def __init__(self, host, port: int = 80):
        self.host = host
        self.port = port

        self.address = f"http://{host}:{port}/api/v1"

        self.job_api = f"{self.address}/job"
        self.result_api = f"{self.address}/result"

        self.endpoints = {
            Endpoint.JOB: self.job_api,
            Endpoint.RESULT: self.result_api
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

