
from sssc.server import Server

class ComputeServer(Server):    

    def __init__(self, host, port: int = 29681):

        self.address = f"http://{host}:{port}"

    @property
    def address(self):
        return self.address


