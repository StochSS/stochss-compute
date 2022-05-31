import sys
import bz2
import time
import inspect

from functools import partial

import plotly.io as plotlyio

from IPython.display import Image

from gillespy2.core import Model
from gillespy2.core import Results

from .compute_server import Endpoint
from .compute_server import ComputeServer

from .remote_utils import unwrap_or_err

from .api.v1.job import ErrorResponse
from .api.v1.job import StartJobResponse
from .api.v1.job import JobStatusResponse
from .api.v1.gillespy2.results import PlotPlotlyRequest
from .api.v1.gillespy2.results import AverageEnsembleRequest

class RemoteResults(Results):
    def __init__(self, result_id: str, server: ComputeServer):
        Results.__new__(Results)

        self.result_id = result_id
        self.server = server
        self.local_results = None

    def __getattribute__(self, name):
        if hasattr(RemoteResults, f"hook_{name}"):
            name = f"hook_{name}"

        return object.__getattribute__(self, name)

    def __poll_job_status(self) -> bool:
        # Request the status of a running job.
        status_response = self.server.get(Endpoint.JOB, f"/{self.result_id}/status")

        if not status_response.ok:
            raise Exception(ErrorResponse.parse_raw(status_response.text).msg)

        # Parse the body of the response into a JobStatusResponse object.
        status = JobStatusResponse.parse_raw(status_response.text)
        print(status.status_msg)
        print(status.status_id)

        return status.is_complete

    def __local_hook(self, target: str = "", *args, **kwargs):
        print(f"Calling proxy for: '{target}'...")
        if self.local_results is None:
            self.local_results = self.resolve()

        return getattr(self.local_results, target)(*args, **kwargs)

    def hook_average_ensemble(self, *args, **kwargs):
        status_response = self.server.get(Endpoint.JOB, f"/{self.result_id}/status")
        status: JobStatusResponse = unwrap_or_err(JobStatusResponse, status_response)

        if status.has_failed:
            raise Exception("Something broke, not sure. Oh well.")

        start_request = AverageEnsembleRequest(result_id=self.result_id)
        start_response: JobStatusResponse = unwrap_or_err(JobStatusResponse, self.server.post(Endpoint.GILLESPY2_RESULTS, "/average_ensemble", request=start_request))

        if start_response.has_failed:
            raise Exception("Something broke.")

        import copy
        test = copy.deepcopy(self)
        test.result_id = start_response.job_id
        test.data = None
        print(test)

        return test

    def hook_plot(self, *args, **kwargs):
        plot_response = self.server.get(Endpoint.RESULT, f"/{self.result_id}/plot")

        if plot_response.status_code == 404:
            raise Exception(plot_response.text)

        print(f"Plot size: {sys.getsizeof(plot_response.content)}")
        plot_image = bz2.decompress(plot_response.content)
        print(f"Expanded to: {sys.getsizeof(plot_image)}")

        return Image(data=plot_image, format="png")

    def hook_plotplotly(self, *args, **kwargs):
        plot_request = PlotPlotlyRequest(result_id=self.result_id)
        plot_response: JobStatusResponse = unwrap_or_err(JobStatusResponse, self.server.post(Endpoint.GILLESPY2_RESULTS, "/plotplotly", request=plot_request))
        
        if plot_response.has_failed:
            raise Exception("Failed to create plotly figure.")

        print(f"Plot size: {sys.getsizeof(plot_response.content)}")
        plot_json = bz2.decompress(plot_response.content).decode()
        print(f"Expanded to: {sys.getsizeof(plot_json)}")

        with open("test", "w") as outfile:
            outfile.write(plot_json)

        plot = plotlyio.from_json(plot_json)
        plot.show()

    def status(self) -> JobStatusResponse:
        """
        Get the status of the remote job.

        :returns: JobStatusResponse
        """

        status_response = self.server.get(Endpoint.JOB, f"/{self.result_id}/status")
        status: JobStatusResponse = unwrap_or_err(JobStatusResponse, status_response)

        return status

    def wait(self):
        """
        Wait for the job to finish.
        """

        while not self.__poll_job_status():
            time.sleep(5)

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

    def cancel(self):
        """
        Cancels the remote job.
        """
        stop_response = self.server.post(Endpoint.JOB, f"/{self.result_id}/stop")

