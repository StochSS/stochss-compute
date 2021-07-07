import time
import json
from typing import Union
import requests

from gillespy2.core import Results

from .api.v1.job import (
    StartJobRequest,
    StartJobResponse,
    JobStatusResponse,
    JobStopResponse,
    ErrorResponse
)

def connect_to(host, port):
    return RemoteSimulation(host, port)

class RemoteSimulation():
    def on(server):
        sim = RemoteSimulation()
        sim.server = server

        return sim

    def with_model(self, model):
        self.model = model

        return self

    def run(self, **params):
        params = json.dumps(params)

        model_hash = self.model.get_json_hash()
        model = self.model.to_json()

        request = StartJobRequest(
            job_id=model_hash,
            model=model
        )

        # Check to see if the job exists.
        exists_response = requests.get(f"{self.server.address}/api/v1/job/{model_hash}/results")
        if exists_response.status_code == 200:
            return Results.from_json(exists_response.text)

        start_raw = requests.post(f"{self.server.address}/api/v1/job/start", json=request.json())

        if start_raw.status_code is not 202:
            print(start_raw)
            error = ErrorResponse.parse_raw(start_raw.text)

            raise Exception(error.msg)

        start_response = StartJobResponse.parse_raw(start_raw.text)

        status_url = f"{self.server.address}/api{start_response.status}"
        print(status_url)
        status_raw = requests.get(status_url)

        if status_raw.status_code is not 200:
            error = ErrorResponse.parse_raw(status_raw.text)
            raise Exception(error.msg)

        job_status = self.__get_job_status(status_url)

        while not job_status.is_complete:
            time.sleep(5)

            job_status = self.__get_job_status(status_url)

        results_raw = requests.get(f"{self.server.address}/api/v1/job/{request.job_id}/results")

        if results_raw.status_code is not 200:
            error = ErrorResponse.parse_raw(results_raw.text)
            raise Exception(error.msg)

        return Results.from_json(results_raw.text)

    def __get_job_status(self, status_url: str) -> JobStatusResponse:
        status_raw = requests.get(status_url)

        if status_raw.status_code is not 200:
            error = ErrorResponse.parse_raw(status_raw.text)
            raise Exception(error)

        return JobStatusResponse.parse_raw(status_raw.text)

class ComputeServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = f"http://{host}:{port}"
