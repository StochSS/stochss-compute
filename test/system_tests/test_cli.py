'''
test.integration_tests.test_api
'''
import os
import subprocess
import time
import unittest

from stochss_compute import RemoteSimulation, ComputeServer


from .gillespy2_models import create_michaelis_menten


class ApiTest(unittest.TestCase):
    '''
    Spins up a local instance for testing.
    '''

    @classmethod
    def setUpClass(cls) -> None:
        cls.api_server = subprocess.Popen('stochss-compute-cluster')

        time.sleep(3)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.api_server.terminate()
        cls.api_server.wait()

    def tearDown(self) -> None:
        for filename in os.listdir('cache'):
            os.remove(f'cache/{filename}')
        return super().tearDown()

    def test_run_resolve(self):
        '''
        Basic function.
        '''
        model = create_michaelis_menten()
        server = ComputeServer('localhost')
        sim = RemoteSimulation(model, server)
        results = sim.run()
        assert(results.data is not None)

    def test_is_cached(self):
        '''
        Test RemoteSimulation#is_cached()
        '''
        model = create_michaelis_menten()
        server = ComputeServer('localhost')
        sim = RemoteSimulation(model, server)
        assert(sim.is_cached() is False)
        results = sim.run()
        results._resolve()
        assert(sim.is_cached() is True)


