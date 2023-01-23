'''
test.unit_tests.test_launch
'''
import os
import subprocess
import time
import unittest
from stochss_compute import ComputeServer


class ComputeServerTest(unittest.TestCase):
    '''
    Test ComputeServer class.
    '''

    def test_init_and_properties(self):
        '''
        Calls init and tests address.
        '''
        server = ComputeServer('cRaZyHoSt.lol', 60095)
        assert server.address == 'http://cRaZyHoSt.lol:60095'
