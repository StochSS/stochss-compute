'''
ComputeServer(Server)
'''
from stochss_compute.client.server import Server

class ComputeServer(Server):
    '''
    Simple object representing a remote instance of StochSS-Compute.

    :param host: Address of the remote server.
    :type host: str

    :param port: Port on which to connect. Defaults to 29681.
    :type port: int
    '''
    # pylint: disable=super-init-not-called
    def __init__(self, host:str, port: int = 29681):
        host = host.replace('http://','')
        host = host.split(':')[0]
        self._address = f"http://{host}:{port}"
    # pylint: enable=super-init-not-called

    @property
    def address(self) -> str:
        """
        The server's IP address and port.
        """
        return self._address
