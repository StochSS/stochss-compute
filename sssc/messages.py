from gillespy2.core import Model
from enum import Enum

class SimStatus(Enum):
    PENDING = 'The simulation is pending.'
    RUNNING = 'The simulation is still running.'
    READY = 'Simulation results are ready to be retrieved.'
    ERROR = 'The Simulation has encountered an error.'
    
class Request:
    pass

class Response:
    pass

class SimulationRunRequest(Request):
    def __init__(self, model: Model, **params):
        self.model = model.to_json()
        self.kwargs = params

class SimulationRunResponse(Response):
    def __init__(self, status: SimStatus, message: str = None):
        self.status = status
        self.message = message
