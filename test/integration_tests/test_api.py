import os
import subprocess
import time
import unittest

from stochss_compute import RemoteSimulation, ComputeServer, start_api


from .gillespy2_models import create_michaelis_menten
from stochss_compute.core.messages import SimStatus

from distributed import Client
import asyncio

class ApiTest(unittest.TestCase):

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
        model = create_michaelis_menten()
        server = ComputeServer('localhost')
        sim = RemoteSimulation(model, server)
        results = sim.run()
        assert(results.data != None)

    def test_isCached(self):
        model = create_michaelis_menten()
        server = ComputeServer('localhost')
        sim = RemoteSimulation(model, server)
        assert(sim.isCached() is False)
        results = sim.run()
        results._resolve()
        assert(sim.isCached() is True)


