
from stochss_compute.client.server import Server

class ComputeServer(Server):    

    def __init__(self, host, port: int = 29681):
        '''
        Simple object representing a remote instance of StochSS-Compute.

        :param host: Address of the remote server.
        :type host: str

        :param port: Port on which to connect. Defaults to 29681.
        :type port: int
        '''
        self._address = f"http://{host}:{port}"

    @property
    def address(self):
        return self._address
    


