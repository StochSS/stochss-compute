import time
import socket
import shutil

from multiprocessing import Process

from tests.gillespy2_models import LacOperon
from tests.gillespy2_models import MichaelisMenten

from stochss_compute import api

from stochss_compute import ComputeServer
from stochss_compute import RemoteSimulation
from stochss_compute.api.delegate import JobState
from stochss_compute.api.delegate import DaskDelegateConfig

import unittest

from distributed import Client
from distributed import Future

class EnsembleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Set up the Dask client and stochss-compute instance.
        cls.client = Client()
        host, port = cls.client.scheduler.address.replace("tcp://", "").split(":")

        delegate_config = DaskDelegateConfig(dask_cluster_address=host, dask_cluster_port=port)

        # If set, change cache root_dir to minimize conflicts.
        if hasattr(delegate_config.cache_provider.config, "root_dir"):
            delegate_config.cache_provider.config.root_dir = "ensemble-test_" + delegate_config.cache_provider.config.root_dir

        cls.api_process = Process(daemon=True, target=api.start_api, kwargs=dict(host="127.0.0.1", port=1234, delegate_config=delegate_config))
        cls.api_process.start()

        cls.compute_server = ComputeServer(host="127.0.0.1", port=1234)

        unittest.addModuleCleanup(cls.cleanupClass)

        time.sleep(3)

    def cleanupClass(self):
        self.client.close()
        self.api_process.terminate()

    def test_job_endpoint_fast_model(self):
        """ Battery of several API endpoints with a quick-to-compute model. """

        job = RemoteSimulation.on(self.compute_server).with_model(MichaelisMenten()).run()

        # Assert that the job hasn't failed yet, and that it does exist on the scheduler.
        assert(job.status().status_id != JobState.FAILED)

        # Wait for the job to complete.
        job.wait()

        # Assert that the API reports status_id as JobState.DONE.
        assert(job.status().status_id == JobState.DONE)
        assert(Future(job.result_id).done)

        # Ensure that the results can be retrieved from the API.
        job_results = job.resolve()

    def test_job_endpoint_slow_model(self):
        job = RemoteSimulation.on(self.compute_server).with_model(LacOperon()).run()
        test = Future(job.result_id)

        # Wait for dependencies to arrive in memory, with timeout.
        for step in range(10):
            if job.status().status_id == JobState.RUNNING:
                break

            if step == 9:
                assert(job.status().status_id == JobState.RUNNING)

            time.sleep(0.5)

        # Assert that the job is currently running.
        assert(job.status().status_id == JobState.RUNNING)

        job.wait()

        assert(job.status().status_id == JobState.DONE)
