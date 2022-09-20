# from stochss_compute.client.server import Server
# figure out type hinting for Server
from stochss_compute.client.endpoint import Endpoint
from gillespy2 import Results

from time import sleep

from tornado.escape import json_decode
from stochss_compute.core.errors import RemoteSimulationError

from stochss_compute.core.messages import ResultsResponse, SimStatus, StatusResponse

class RemoteResults(Results):
    """
    Wrapper for a gillespy2.Results object that exists on a remote server and which is then downloaded locally.
    A Results object is: A List of Trajectory objects created by a gillespy2 solver, extends the UserList object.

    :param data: A list of trajectory objects.
    :type data: UserList

    :param id: ID of the cached Results object.
    :type id: str

    :param server: The remote instance of StochSS-Compute where the Results are cached.
    :type server: stochss_compute.ComputeServer
    """

    id = None
    server = None

    def __init__(self, data = None):

        self._data = data

    @property
    def data(self):
        if self.id is None or self.server is None:
            raise Exception('RemoteResults must have a self.id and a self.server.')

        if self._data is None:
            self._resolve()
        return self._data


    def _status(self):
        # Request the status of a running job.
        response_raw = self.server.get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/status")
        if not response_raw.ok:
            raise Exception(response_raw.reason)

        status_response = StatusResponse.parse(response_raw.text)
        return status_response

    def _resolve(self):
        status_response = self._status()
        status = status_response.status
        if status == SimStatus.PENDING:
            print('Simulation is pending (not running yet). Checking for status update....')
            while True:
                sleep(5)
                status_response = self._status()
                status = status_response.status
                if status != SimStatus.PENDING:
                    break

        if status == SimStatus.RUNNING:
            print('Simulation is running. Downloading results when complete......')
            while True:
                sleep(5)
                status_response = self._status()
                status = status_response.status
                if status == SimStatus.PENDING:
                    raise Exception('Unknown Error.')
                if status != SimStatus.RUNNING:
                    break

        if status == SimStatus.ERROR:
            raise RemoteSimulationError(status_response.error_message)

        if status == SimStatus.READY:
            print('Results ready. Fetching.......')
            response_raw = self.server.get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/results")
            if not response_raw.ok:
                raise Exception(response_raw.reason)

            response = ResultsResponse.parse(response_raw.text)
            self._data = response.results.data


    def ready(self):
        return self._status().status == SimStatus.READY

    def error(self):
        status_response = self._status()
        # raise error by grabbing error class from task and put into response object

    def plot(self, index=None, xaxis_label="Time", xscale='linear', yscale='linear', yaxis_label="Value",
            style="default", title=None, show_title=False, show_legend=True, multiple_graphs=False,
            included_species_list=[], save_png=False, figsize=(18, 10)):
        """
        Plots the Results using matplotlib.

        :param index: If not none, the index of the Trajectory to be plotted.
        :type index: int

        :param xaxis_label: The label for the x-axis
        :type xaxis_label: str

        :param yaxis_label: The label for the y-axis
        :type yaxis_label: str
        
        :param title: The title of the graph
        :type title: str
        
        :param multiple_graphs: IF each trajectory should have its own graph or if they should overlap.
        :type multiple_graphs: bool
        
        :param included_species_list: A list of strings describing which species to include. By default displays all
            species.
        :type included_species_list: list
        
        :param save_png: Should the graph be saved as a png file. If True, File name is title of graph. If a string is
            given, file is named after that string.
        :type save_png: bool or str
        
        :param figsize: The size of the graph. A tuple of the form (width,height). Is (18,10) by default.
        :type figsize: tuple of ints (x,y)
        """
        super.plot(index=index, xaxis_label=xaxis_label, xscale=xscale, yscale=yscale, yaxis_label=yaxis_label,
             style=style, title=title, show_title=show_title, show_legend=show_legend, multiple_graphs=multiple_graphs,
             included_species_list=included_species_list, save_png=save_png, figsize=figsize)
