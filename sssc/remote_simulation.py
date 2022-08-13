import bz2
import sys

import plotly.io as plotlyio

from gillespy2.core import Model, GillesPySolver

from sssc.errors import RemoteSimulationError

from .remote_utils import unwrap_or_err

from .server import Endpoint
from .server import ComputeServer

from .remote_results import RemoteResults

from .api.v1.gillespy2.model import ModelRunRequest

from .api.v1.job import (
    StartJobRequest,
    StartJobResponse,
    JobStatusResponse,
    JobStopResponse,
    ErrorResponse
)

class RemoteSimulation:

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
                 seed: int = None,
                 
                 **solver_args
                 ) -> None:

        if server is not None and server_host is not None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host but not both.')
        if server is None and server_host is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or host.')
        if server is None and server_port is None:
            raise RemoteSimulationError('Pass a ComputeServer/Cluster object or port.')

    def run(self):
        pass

