from compute_server import ComputeServer
from server import Server
from errors import RemoteSimulationError

from gillespy2.core import GillesPySolver, Model

from messages import SimulationRunRequest, SimulationRunResponse, SimStatus
from server import Endpoint

from tornado.escape import json_decode

class RemoteSimulation:
    # TODO accept arguments in constructor, but override in run?

    def __init__(self,
                 model: Model = None,
                 server: Server = None,
                 host: str = None,
                 port: int = 29681,
                 solver: GillesPySolver = None,
                 ) -> None:

        if server is not None and host is not None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host but not both.')
        if server is None and host is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host.')
        if server is None and port is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or port.')

        if server is None:
            self.server = ComputeServer(host, port)
        else:
            self.server = server

        self.model = model
        

    def run(self, **params):
        """
        Simulate the Model on the target ComputeServer, returning the results once complete.

        :param **params: Arguments to pass directly to the Model#run call on the server.
        
        :returns: Results
        """
    
        if "solver" in params:
            params["solver"] = f"{params['solver'].__module__}.{params['solver'].__qualname__}"

        sim_request = SimulationRunRequest(model=self.model, kwargs=params)
        response_raw = self.server.post(Endpoint.SIMULATION_GILLESPY2, sub="/run", request=sim_request)

        if not response_raw.ok:
            raise Exception(response_raw.reason)

        sim_response: SimulationRunResponse = json_decode(response_raw.text)

        if sim_response.status == SimStatus.ERROR:
            raise RemoteSimulationError(sim_response.message)

        return sim_response.results



