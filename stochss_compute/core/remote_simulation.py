from stochss_compute.client.endpoint import Endpoint
from stochss_compute.core.messages import SimulationRunRequest, SimulationRunResponse, SimStatus
from stochss_compute.core.errors import RemoteSimulationError

from gillespy2 import GillesPySolver, Model

from tornado.escape import json_decode

from stochss_compute.core.remote_results import RemoteResults

class RemoteSimulation:
    # TODO accept arguments in constructor, but override in run?
    # removed type hinting for server due to circular import
    def __init__(self,
                 model: Model = None,
                 server = None,
                 host: str = None,
                 port: int = 29681,
                 solver = None,
                 ) -> None:

        if server is not None and host is not None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host but not both.')
        if server is None and host is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host.')
        if server is None and port is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or port.')

        if server is None:
            from stochss_compute.client.compute_server import ComputeServer
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

        sim_response = SimulationRunResponse.parse(response_raw.text)
        
        if sim_response.status == SimStatus.ERROR:
            raise RemoteSimulationError(sim_response.message)
            # If sim throws an error, would we still need to be able to interact with it in any way? like to clear it from memory or restart a worker?
        if sim_response.status == SimStatus.READY:
            return RemoteResults(id=sim_response.results_id, server=self.server, results=sim_response.results)
        else:
            return RemoteResults(id=sim_response.results_id, server=self.server)



