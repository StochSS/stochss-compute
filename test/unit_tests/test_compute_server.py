'''
test.unit_tests.test_launch
'''
import unittest
from stochss_compute import ComputeServer
from stochss_compute.client.server import Server
from stochss_compute.client.endpoint import Endpoint
from stochss_compute.core.messages import SimulationRunRequest
from .gillespy2_models import create_decay

class ComputeServerTest(unittest.TestCase):
    '''
    Test ComputeServer class.
    '''
    def setUp(self) -> None:
        self.server = ComputeServer('cRaZyHoSt.lol', 60095)
        self.sim_endpoint = Endpoint.SIMULATION_GILLESPY2

    def test_init_and_properties(self):
        '''
        Calls init and tests address.
        '''
        assert self.server.address == 'http://cRaZyHoSt.lol:60095'

    def test_get(self):
        '''
        calls get to timeout
        '''
        self.server.get(self.sim_endpoint,'')

    def test_post(self):
        '''
        calls post to timeout
        '''
        server = ComputeServer('cRaZyHoSt.lol', 60095)
        sim_endpoint = Endpoint.SIMULATION_GILLESPY2
        server.post(sim_endpoint,'', SimulationRunRequest(create_decay()))

    def test_super_error(self):
        '''
        Error to instantiate superclass.
        '''
        self.assertRaises(TypeError, Server)