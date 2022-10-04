from stochss_compute.client.endpoint import Endpoint
from stochss_compute.core.messages import SimulationRunRequest, SimulationRunResponse, SimStatus
from stochss_compute.core.errors import RemoteSimulationError

from stochss_compute.core.remote_results import RemoteResults

class RemoteSimulation:
    '''
    An object representing a remote gillespy2 simulation. Requires a model and a host address.
    A solver type may be provided, but does not accept instantiated solvers. 

    :param model: The model to simulate.
    :type model: gillespy2.Model

    :param server: A server to run the simulation. Optional if host is provided.
    :type server: stochss_compute.Server

    :param host: The address of a running instance of StochSS-Compute. Optional if server is provided.
    :type host: str

    :param port: The port to use when connecting to the host. Only needed if default server port is changed. Defaults to 29681.
    :type port: int

    :param solver: The type of solver to use or the name of a solver. Does not accept instantiated solvers.
    :type solver: Type[gillespy2.GillesPySolver]


    '''
    def __init__(self,
                 model,
                 server = None,
                 host: str = None,
                 port: int = 29681,
                 solver = None,
                 ):

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

        if solver is not None:
            if hasattr(solver, 'is_instantiated'):
                raise RemoteSimulationError('RemoteSimulation does not accept an instantiated solver object. Pass a type.')
        self.solver = solver
        

    def run(self, **params):
        """
        Simulate the Model on the target ComputeServer, returning the results once complete.
        See: https://stochss.github.io/GillesPy2/docs/build/html/classes/gillespy2.core.html#gillespy2.core.model.Model.run

        :param **params: Arguments to pass directly to the Model#run call on the server.
        
        :returns: stochss_compute.RemoteResults
        """
    
        if "solver" in params:
            params["solver"] = f"{params['solver'].__module__}.{params['solver'].__qualname__}"
        if self.solver is not None:
            params["solver"] = f"{self.solver.__module__}.{self.solver.__qualname__}"

        sim_request = SimulationRunRequest(model=self.model, kwargs=params)
        response_raw = self.server.post(Endpoint.SIMULATION_GILLESPY2, sub="/run", request=sim_request)
        if not response_raw.ok:
            raise Exception(response_raw.reason)

        sim_response = SimulationRunResponse.parse(response_raw.text)
        
        if sim_response.status == SimStatus.ERROR:
            raise RemoteSimulationError(sim_response.message)
            # If sim throws an error, would we still need to be able to interact with it in any way? like to clear it from memory or restart a worker?
        if sim_response.status == SimStatus.READY:
            remote_results =  RemoteResults(data=sim_response.results.data)
        else:
            remote_results =  RemoteResults()
            
        remote_results.id = sim_response.results_id
        remote_results.server = self.server

        return remote_results
