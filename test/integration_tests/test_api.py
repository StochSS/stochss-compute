import subprocess
import time
import unittest
import tempfile

from stochss_compute import RemoteSimulation, ComputeServer

from gillespy2_models import create_robust_model
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


    def test_run_and_resolve(self):
        model = create_robust_model()
        server = ComputeServer('localhost')
        sim = RemoteSimulation(model, server=server)
        results = sim.run()
        status_response = results._status()
        assert(status_response.status == SimStatus.RUNNING)
        assert(status_response.error_message == None)
        results._resolve()
        assert(results.ready())
