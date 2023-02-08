'''
stochss_compute.core.remote_results
'''
from time import sleep
from gillespy2 import Results
from stochss_compute.client.endpoint import Endpoint
from stochss_compute.core.errors import RemoteSimulationError
from stochss_compute.core.messages import ResultsResponse, SimStatus, StatusResponse

class RemoteResults(Results):
    '''
    Wrapper for a gillespy2.Results object that exists on a remote server and which is then downloaded locally.
    A Results object is: A List of Trajectory objects created by a gillespy2 solver, extends the UserList object.

    These three fields must be initialized manually: id, server, n_traj, task_id.

    :param data: A list of trajectory objects.
    :type data: UserList

    :param id: ID of the cached Results object.
    :type id: str

    :param server: The remote instance of StochSS-Compute where the Results are cached.
    :type server: stochss_compute.ComputeServer

    :param task_id: Handle for the running simulation.
    :type task_id: str
    '''
    # These three fields are initialized by the server
    id = None
    server = None
    n_traj = None
    task_id = None

    def __init__(self, data = None):
        self._data = data

    @property
    def data(self):
        """
        The trajectory data.

        :returns: self._data
        :rtype: UserList
        """
        if None in (self.id, self.server, self.n_traj):
            raise Exception('RemoteResults must have a self.id, self.server and self.n_traj.')

        if self._data is None:
            self._resolve()
        return self._data

    @property
    def sim_status(self):
        '''
        Fetch the simulation status.

        :returns: Simulation status enum as a string.
        :rtype: str
        '''
        return self._status().status.name

    def get_gillespy2_results(self):
        """
        Get the GillesPy2 results object from the remote results.

        :returns: The generated GillesPy2 results object.
        :rtype: gillespy.Results
        """
        return Results(self.data)


    @property
    def is_ready(self):
        """
        True if results exist in cache on the server.

        :returns: status == SimStatus.READY
        :rtype: bool
        """
        return self._status().status == SimStatus.READY

    def _status(self):
        # Request the status of a submitted simulation.
        response_raw = self.server.get(Endpoint.SIMULATION_GILLESPY2,
                                       f"/{self.id}/{self.n_traj}/{self.task_id or ''}/status")
        if not response_raw.ok:
            raise RemoteSimulationError(response_raw.reason)

        status_response = StatusResponse.parse(response_raw.text)
        return status_response

    def _resolve(self):
        status_response = self._status()
        status = status_response.status

        if status == SimStatus.RUNNING:
            print('Simulation is running. Downloading results when complete......')
            while True:
                sleep(5)
                status_response = self._status()
                status = status_response.status
                if status != SimStatus.RUNNING:
                    break

        if status in (SimStatus.DOES_NOT_EXIST, SimStatus.ERROR):
            raise RemoteSimulationError(status_response.message)


        if status == SimStatus.READY:
            print('Results ready. Fetching.......')
            response_raw = self.server.get(Endpoint.SIMULATION_GILLESPY2, f"/{self.id}/{self.n_traj}/results")
            if not response_raw.ok:
                raise RemoteSimulationError(response_raw.reason)

            response = ResultsResponse.parse(response_raw.text)
            self._data = response.results.data

