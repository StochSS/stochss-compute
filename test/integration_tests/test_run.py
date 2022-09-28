import asyncio
import subprocess
import time
import unittest
import tempfile

from threading import Thread

from stochss_compute.server import api

from stochss_compute import RemoteSimulation

from distributed import Client
from distributed import Future
from distributed import LocalCluster

from stochss_compute import launch
from gillespy2_models import create_robust_model

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


    def test_run(self):
        model = create_robust_model()
        sim = RemoteSimulation(model, host='localhost')
        results = sim.run()
        assert(results.server != None)