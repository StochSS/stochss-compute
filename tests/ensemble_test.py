import time
import shutil
from threading import Thread

from tests.gillespy2_models import LacOperon
from tests.gillespy2_models import MichaelisMenten

from stochss_compute import api

from stochss_compute import ComputeServer
from stochss_compute import RemoteSimulation
from stochss_compute.api.delegate import JobState
from stochss_compute.api.delegate import DaskDelegateConfig

import pytest

from distributed import Client
from distributed import Future

@pytest.fixture(scope="session")
def cluster_client():
    # Set up the Dask client and stochss-compute instance.
    client = Client(heartbeat_interval=200, set_as_default=False)

    host, port = client.scheduler.address.replace("tcp://", "").split(":")
    delegate_config = DaskDelegateConfig(dask_cluster_address=host, dask_cluster_port=port)

    # If set, change cache root_dir to minimize conflicts.
    if hasattr(delegate_config.cache_provider.config, "root_dir"):
        delegate_config.cache_provider.config.root_dir = "ensemble-test_" + delegate_config.cache_provider.config.root_dir

    api_process = Thread(daemon=True, target=api.start_api, kwargs=dict(host="0.0.0.0", port=1234, delegate_config=delegate_config))
    api_process.start()

    time.sleep(1)

    yield client

    # Cleanup on closure, ensuring cache directory and dask-worker-space are removed.
    client.close()
    shutil.rmtree(delegate_config.cache_provider.config.root_dir)

@pytest.fixture()
def compute_server(cluster_client: Client):
    yield ComputeServer(host="0.0.0.0", port=1234)

def test_job_endpoint_fast_model(cluster_client: Client, compute_server: ComputeServer):
    """ Battery of several API endpoints with a quick-to-compute model. """

    job = RemoteSimulation.on(compute_server).with_model(MichaelisMenten()).run()

    # Assert that the job hasn't failed yet, and that it does exist on the scheduler.
    assert(job.status().status_id != JobState.FAILED)

    # Wait for the job to complete.
    job.wait()

    # Assert that the API reports status_id as JobState.DONE.
    assert(job.status().status_id == JobState.DONE)
    assert(Future(job.result_id).done)

    # Ensure that the results can be retrieved from the API.
    job_results = job.resolve()

def test_job_endpoint_slow_model(cluster_client: Client, compute_server: ComputeServer):
    job = RemoteSimulation.on(compute_server).with_model(LacOperon()).run()
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