from sssc.compute_server import ComputeServer
from sssc.errors import RemoteSimulationError

from gillespy2.core import GillesPySolver, Model

class RemoteSimulation:
    # TODO accept arguments in constructor, but override in run

    def __init__(self,
                 model: Model = None,
                 server = None,
                 server_host: str = None,
                 server_port: int = 29681,
                 solver: GillesPySolver = None,
                 algorithm: str = None,
                 timeout: int = None,
                 t: int = None,
                 increment: int = None,
                 number_of_trajectories = None,
                 seed: int = None,
                 **solver_args,
                 ) -> None:

        if server is not None and server_host is not None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host but not both.')
        if server is None and server_host is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host.')
        if server is None and server_port is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or port.')

        if server is None:
            self.server = ComputeServer(server_host, server_port)
        else:
            self.server = server
        
        
    def run(self):

        pass

