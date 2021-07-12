import sys
import bz2
import time

import plotly.io as plotlyio

from gillespy2.core import Model
from gillespy2.core import Results

from .remote_utils import unwrap_or_err

from .compute_server import Endpoint
from .compute_server import ComputeServer

from .api.v1.job import ErrorResponse
from .api.v1.job import JobStatusResponse

class RemoteResults(Results):
    def __init__(self, result_id: str, server: ComputeServer, model: Model):
        self.result_id = result_id
        self.server = server
        self.model = model

    def __poll_job_status(self) -> bool:
        # Request the status of a running job.
        status_response = self.server.get(Endpoint.JOB, f"/{self.result_id}/status")

        if not status_response.ok:
            raise Exception(ErrorResponse.parse_raw(status_response.text).msg)

        # Parse the body of the response into a JobStatusResponse object.
        status = JobStatusResponse.parse_raw(status_response.text)

        return status.is_complete

    def status(self) -> JobStatusResponse:
        """
        Get the status of the remote job.

        :returns: JobStatusResponse
        """

    def resolve(self) -> Results:
        """
        Finish the remote job and return the results.
        This function will block until the remote job is complete.

        :returns: Results
        """

        # Poll the job status until it finishes.
        while not self.__poll_job_status():
            time.sleep(5)

        # Request the results of the finished job.
        results_response = self.server.get(Endpoint.RESULT, f"/{self.result_id}/get")

        if not results_response.ok:
            raise Exception(ErrorResponse.parse_raw(results_response.text).msg)

        print(f"Results size: {sys.getsizeof(results_response.content)}")
        results_json = bz2.decompress(results_response.content).decode()
        print(f"Expanded to: {sys.getsizeof(results_json)}")

        # Parse and return the response body into a valid Results object.
        results = Results.from_json(results_json)

        return results

    def hook_plotplotly(self, *args, **kwargs):
        plot_response = self.server.get(Endpoint.RESULT, f"/{self.result_id}/plotplotly")
        
        print(f"Plot size: {sys.getsizeof(plot_response.content)}")
        plot_json = bz2.decompress(plot_response.content).decode()
        print(f"Expanded to: {sys.getsizeof(plot_json)}")

        with open("test", "w") as outfile:
            outfile.write(plot_json)

        plot = plotlyio.from_json(plot_json)
        plot.show()

