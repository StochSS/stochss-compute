import os
import subprocess
import time
import unittest

from stochss_compute import RemoteSimulation, ComputeServer

from gillespy2_models import create_michaelis_menten
from stochss_compute.core.messages import SimStatus

class ApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:

        cmd = ["stochss-compute-cluster"]
        cls.api_server = subprocess.Popen(cmd)

        time.sleep(3)

    @classmethod
    def tearDownClass(cls) -> None:
        
        cls.api_server.terminate()

    def tearDown(self) -> None:
        for filename in os.listdir('cache'):
            os.remove(f'cache/{filename}')
        return super().tearDown()

    def test_run_resolve_cache(self):
        model1 = create_michaelis_menten()
        server = ComputeServer('localhost')
        sim1 = RemoteSimulation(model1, server)
        results1 = sim1.run()
        status_response = results1._status()
        assert(status_response.status != SimStatus.ERROR)
        assert(status_response.error_message == None)
        results1._resolve()
        assert(results1.isReady)

        model2 = create_michaelis_menten()
        sim2 = RemoteSimulation(model2, server)
        results2 = sim2.run()
        assert(results2._data != None)
        assert(results2.id == results1.id)

    # @unittest.skip('fix this')
    def test_isCached(self):
        model = create_michaelis_menten()
        server = ComputeServer('localhost')
        sim = RemoteSimulation(model, server)
        assert(sim.isCached() is False)
        results = sim.run()
        results._resolve()
        assert(sim.isCached() is True)

