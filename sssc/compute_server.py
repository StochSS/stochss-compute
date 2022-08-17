
from server import Server

class ComputeServer(Server):    

    def __init__(self, host, port: int = 29681):

        self._address = f"http://{host}:{port}"

    @property
    def address(self):
        return self._address
    


