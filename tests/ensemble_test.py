import time
import unittest
import tempfile

from threading import Thread

from tests.gillespy2_models import LacOperon
from tests.gillespy2_models import MichaelisMenten

from stochss_compute import api

from stochss_compute import ComputeServer
from stochss_compute import RemoteSimulation
from stochss_compute.api.delegate import JobState
from stochss_compute.api.delegate import DaskDelegateConfig

from distributed import Client
from distributed import Future
from distributed import LocalCluster

class EnsembleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cache_dir = tempfile.TemporaryDirectory(suffix="stochss-compute_")
        cls.worker_dir = tempfile.TemporaryDirectory(suffix="stochss-compute_")

        # Set up the Dask client and stochss-compute instance.
        cls.cluster = LocalCluster("127.0.0.1:9797", local_directory=cls.worker_dir.name)
        cls.client = Client(address=cls.cluster.scheduler_address, set_as_default=False)

        host, port = cls.client.scheduler.address.replace("tcp://", "").split(":")

        delegate_config = DaskDelegateConfig(dask_cluster_address=host, dask_cluster_port=port)

        # If set, change cache root_dir to minimize conflicts.
        if hasattr(delegate_config.cache_provider.config, "root_dir"):
            delegate_config.cache_provider.config.root_dir = cls.cache_dir.name

        cls.api_process = Thread(daemon=False, target=api.start_api, kwargs=dict(host="127.0.0.1", port=29681, delegate_config=delegate_config))
        cls.api_process.start()

        cls.compute_server = ComputeServer(host="127.0.0.1", port=29681)

        time.sleep(3)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.cluster.close()
        cls.client.close()

        cls.cache_dir.cleanup()
        cls.worker_dir.cleanup()

    def test_run_model_consistency(self):
        """ Test to ensure the API and Cluster return consistent job statuses. """
        
        model = MichaelisMenten()
        model.name = "test_run_model_consistency_MichaelisMenten"

        job = RemoteSimulation.on(self.compute_server).with_model(model).run()

        # Assert that the job hasn't failed yet, and that it does exist on the scheduler.
        assert(job.status().status_id != JobState.FAILED)

        # Wait for the job to complete.
        job.wait()

        # Assert that the API reports status_id as JobState.DONE.
        assert(job.status().status_id == JobState.DONE)

        # Assert that results can be retrieved from the API. This will raise an exception if the request fails.
        Future(job.result_id, client=self.client).result(timeout=5)

    @unittest.skip("Currently broken due to invalid job stop behavior. See issue #61 for more details.")
    def test_job_stop(self):
        """ Test to ensure that running jobs can be stopped. """

        job = RemoteSimulation.on(self.compute_server).with_model(LacOperon()).run()
        time.sleep(5)

        # Stop the job and assert that the API and Cluster report it as removed.
        job.cancel()

        # Assert that the stopped job can no longer be resolved.
        self.assertRaises(Exception, job.resolve())

    @unittest.skip("Broken due to invalid internal result resolution behavior. See issue #62 for more details.")
    def test_job_cache(self):
        """ Test the cache behavior for completed jobs. """

        model = MichaelisMenten()
        model.namee = "test_job_cache_MichaelisMenten"

        job = RemoteSimulation.on(self.compute_server).with_model(model).run()

        # Wait for the job to complete and get the results.
        results = job.resolve().to_json()

        # Assert that results can still be resolved even if the job was cancelled.
        Future(job.result_id, client=self.client).cancel()
        assert(results == job.resolve().to_json())

        # Assert that job results can be resolved from the cache.
        self.client.unpublish_dataset(job.result_id)
        assert(results == job.resolve().to_json())
