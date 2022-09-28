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
        cls.cache_dir = tempfile.TemporaryDirectory(prefix="stochss-compute_")
        cls.worker_dir = tempfile.TemporaryDirectory(prefix="stochss-compute_")

        cmd = ["stochss-compute-cluster"]
        cls.api_server = subprocess.Popen(cmd)

        time.sleep(3)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.cache_dir.cleanup()
        cls.worker_dir.cleanup()
        
        cls.api_server.terminate()
        cls.api_server.wait()


    def test_run_status(self):
        model = create_robust_model()
        server = ComputeServer('localhost')
        sim = RemoteSimulation(model, server=server)
        self.results = sim.run()
        status_response = self.results._status()
        assert(status_response.status == SimStatus.RUNNING)
        assert(status_response.error_message == None)