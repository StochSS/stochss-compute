import bz2
import sys
import json

import plotly.io as plotlyio

from gillespy2.core import Model
from gillespy2.core import Results

from .remote_utils import unwrap_or_err

from .compute_server import Endpoint
from .compute_server import ComputeServer

from .remote_results import RemoteResults

from .api.v1.job import (
    StartJobRequest,
    StartJobResponse,
    JobStatusResponse,
    JobStopResponse,
    ErrorResponse
)

class RemoteSimulation():
    @classmethod
    def on(cls, server: ComputeServer):
        """
        Specify a stochss-compute server that subsequent simulations will be run on.

        :param server: A ComputeServer instance which contains connection details
            of the stochss-compute instance to run simulations on.
        :type server: ComputeServer
        """

        return RemoteSimulation(server)

    def __init__(self, server: ComputeServer):
        self.server = server

    def with_model(self, model: Model):
        """
        Specify the GillesPy2 Model that will be run in subquent simulations.

        :param model: The GillesPy2 Model to simulate.
        :type model: Model
        """

        self.model = model

        return self

    def run(self, **params) -> RemoteResults:
        """
        Simulate the Model on the target ComputeServer, returning the results once complete.

        :param **params: Arguments to pass directly to the Model#run call on the server.
        
        :returns: Results
        """

        params = json.dumps(params)

        model_hash = self.model.get_json_hash()
        model = self.model.to_json()

        remote_results = RemoteResults(result_id=model_hash, server=self.server, model=self.model)

        # Check to see if results already exist for this ID.
        results_response = self.server.get(Endpoint.RESULT, f"/{model_hash}/exists")

        # If this query returns a 200 then a result with this ID exists.
        if results_response.ok:
            return remote_results 

        # Get the status of a job with this ID.
        status_response = self.server.get(Endpoint.JOB, f"/{model_hash}/status")

        # If the job exists and it hasn't failed, return the RemoteResult.
        if status_response.ok and not JobStatusResponse.parse_raw(status_response.text).has_failed:
            return remote_results

        # If we make it this far then the job either doesn't exist or has failed. Either way, start a new one.
        start_request = StartJobRequest(job_id=model_hash, model=model)
        start_response = self.server.post(Endpoint.JOB, "/start", request=start_request)

        # Attempt to unwrap the response. If the request failed though, raise an Exception.
        unwrap_or_err(StartJobResponse, start_response)

        # Looks like everything went well, return the RemoteResult.
        return remote_results

    def test_plot(self):
        plot_response = self.server.get(Endpoint.RESULT, f"/{self.model.get_json_hash()}/plot")
        # plot_request = requests.get(f"{self.server.address}/api/v1/result/{self.model.get_json_hash()}/plot")

        print(f"Plot size: {sys.getsizeof(plot_response.content)}")
        plot_json = bz2.decompress(plot_response.content).decode()

        with open("test", "w") as outfile:
            outfile.write(plot_json)

        plot = plotlyio.from_json(plot_json)
        plot.show()

    def __get_job_status(self, status_url: str) -> JobStatusResponse:
        status_response  = self.server.get(Endpoint.JOB, status_url)
        # status_raw = requests.get(status_url)

        if status_response.status_code != 200:
            error = ErrorResponse.parse_raw(status_response.text)
            raise Exception(error)

        return JobStatusResponse.parse_raw(status_response.text)

