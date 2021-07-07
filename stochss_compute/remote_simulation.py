import time
import json
import requests

from gillespy2.core import Model
from gillespy2.core import Results

from .api.v1.job import (
    StartJobRequest,
    StartJobResponse,
    JobStatusResponse,
    JobStopResponse,
    ErrorResponse
)

class ComputeServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = f"http://{host}:{port}"

class RemoteSimulation():
    @classmethod
    def on(cls, server: ComputeServer):
        """
        Specify a stochss-compute server that subsequent simulations will be run on.

        :param server: A ComputeServer instance which contains connection details
            of the stochss-compute instance to run simulations on.
        :type server: ComputeServer
        """

        sim = RemoteSimulation()
        sim.server = server

        return sim

    def with_model(self, model: Model):
        """
        Specify the GillesPy2 Model that will be run in subquent simulations.

        :param model: The GillesPy2 Model to simulate.
        :type model: Model
        """

        self.model = model

        return self

    def run(self, **params) -> Results:
        """
        Simulate the Model on the target ComputeServer, returning the results once complete.

        :param **params: Arguments to pass directly to the Model#run call on the server.
        
        :returns: Results
        """

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

        if start_raw.status_code != 202:
            print(start_raw)
            error = ErrorResponse.parse_raw(start_raw.text)

            raise Exception(error.msg)

        start_response = StartJobResponse.parse_raw(start_raw.text)

        status_url = f"{self.server.address}/api{start_response.status}"
        print(status_url)
        status_raw = requests.get(status_url)

        if status_raw.status_code != 200:
            error = ErrorResponse.parse_raw(status_raw.text)
            raise Exception(error.msg)

        job_status = self.__get_job_status(status_url)

        while not job_status.is_complete:
            time.sleep(5)

            job_status = self.__get_job_status(status_url)

        results_raw = requests.get(f"{self.server.address}/api/v1/job/{request.job_id}/results")

        if results_raw.status_code != 200:
            error = ErrorResponse.parse_raw(results_raw.text)
            raise Exception(error.msg)

        return Results.from_json(results_raw.text)

    def __get_job_status(self, status_url: str) -> JobStatusResponse:
        status_raw = requests.get(status_url)

        if status_raw.status_code != 200:
            error = ErrorResponse.parse_raw(status_raw.text)
            raise Exception(error)

        return JobStatusResponse.parse_raw(status_raw.text)

