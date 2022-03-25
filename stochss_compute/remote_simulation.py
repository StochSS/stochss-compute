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

from .api.v1.gillespy2.model import ModelRunRequest

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
    
        if "solver" in params:
            params["solver"] = f"{params['solver'].__module__}.{params['solver'].__qualname__}"

        start_request = ModelRunRequest(model=self.model, kwargs=params)
        start_response = unwrap_or_err(JobStatusResponse, self.server.post(Endpoint.GILLESPY2_MODEL, sub="/run", request=start_request))

        remote_results = RemoteResults(result_id=start_response.job_id, server=self.server)
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

