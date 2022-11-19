# from stochss_compute.client.server import Server
# figure out type hinting for Server
from stochss_compute.client.endpoint import Endpoint
from gillespy2 import Results

from time import sleep

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
        """
        The trajectory data.
        """
        if self.id is None or self.server is None:
            raise Exception('RemoteResults must have a self.id and a self.server.')

        if self._data is None:
            self._resolve()
        return self._data

    @property
    def simStatus(self):
        return self._status().status.name


    def _status(self):
        # Request the status of a submitted simulation.
        response_raw = self.server._get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/status")
        if not response_raw.ok:
            raise RemoteSimulationError(response_raw.reason)

        status_response = StatusResponse._parse(response_raw.text)
        return status_response

    def _resolve(self):
        status_response = self._status()
        status = status_response.status
        if status == SimStatus.PENDING or status == SimStatus.DOES_NOT_EXIST:
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
                    continue
                if status != SimStatus.RUNNING:
                    break

        if status == SimStatus.ERROR:
            raise RemoteSimulationError(status_response.error_message)

        if status == SimStatus.READY:
            print('Results ready. Fetching.......')
            response_raw = self.server._get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/results")
            if not response_raw.ok:
                raise RemoteSimulationError(response_raw.reason)

            response = ResultsResponse._parse(response_raw.text)
            self._data = response.results.data


    def get_gillespy2_results(self):
        """
        Get the GillesPy2 results object from the remote results.

        :returns: The generated GillesPy2 results object.
        :rtype: gillespy.Results
        """
        return Results(self.data)


    @property
    def isReady(self):
        """
        True if results exist in cache on the server.
        """
        return self._status().status == SimStatus.READY

