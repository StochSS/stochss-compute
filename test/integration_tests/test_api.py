import os
import subprocess
import time
import unittest

from stochss_compute import RemoteSimulation, ComputeServer

from gillespy2_models import create_michaelis_menten
from stochss_compute.core.messages import SimStatus

from distributed import Client

class ApiTest(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = Client()
        dask_scheduler_port = cls.client.scheduler.addr.split(":")[2]
        # asyncio.run(start_api())
        cmd = ["stochss-compute", "--dask-scheduler-port", dask_scheduler_port]
        cls.api_server = subprocess.Popen(cmd)
        print(cls.api_server.pid)

        time.sleep(3)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tear_down()

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

    @classmethod
    async def tear_down(cls):
        cls.api_server.kill()
        await cls.api_server.wait()
        await cls.client.shutdown()
        await cls.client.close()

