import subprocess
import time
import unittest
import tempfile

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


    def test_run_resolve_cache(self):
        model1 = create_michaelis_menten()
        server = ComputeServer('localhost')
        sim1 = RemoteSimulation(model1, server)
        results1 = sim1.run()
        status_response = results1._status()
        assert(status_response.status == SimStatus.RUNNING)
        assert(status_response.error_message == None)
        results1._resolve()
        assert(results1.ready())

        model2 = create_michaelis_menten()
        sim2 = RemoteSimulation(model2, server)
        results2 = sim2.run()
        assert(results2._data != None)
        assert(results2.id == results1.id)
