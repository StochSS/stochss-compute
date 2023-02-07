import multiprocessing as mp
import unittest
from stochss_compute import start_api
from distributed import Client
class RunHandlerTest(unittest.TestCase):
    sssc = None
    dask = None
    def setUp(self) -> None:
        self.dask = Client()
        dask_scheduler_port = self.dask.scheduler.addr.split(":")[2]
        self.sssc = mp.Process(target=start_api, args={'dask_scheduler_port':dask_scheduler_port})
# import asyncio
# import subprocess, os
# from stochss_compute.client.compute_server import ComputeServer
# from stochss_compute.core.remote_simulation import RemoteSimulation

# class TestRunHandler(IsolatedAsyncioTestCase):
#     events = []
#     _dask_cluster = None
#     cache_dir = 'cache/'
#     host = 'localhost'
#     port = 9999
#     def tearDown(self) -> None:
#         self.events.append("tearDown")
#         if os.path.exists(self.cache_dir):
#             r_m = subprocess.Popen(['rm', '-r', self.cache_dir])
#             r_m.wait()

# '''
# test.integration_tests.test_api
# '''
# import os, asyncio
# import subprocess
# import time
# import unittest

# from stochss_compute import RemoteSimulation, ComputeServer


# from .gillespy2_models import create_michaelis_menten
# from distributed import Client
# from stochss_compute.server.api import start_api
# from unittest import IsolatedAsyncioTestCase


# class RunHandlerTest(unittest.TestCase):
#     '''
#     Spins up a local instance for testing.
#     '''
#     sssc = None
#     dask = None
#     async def asyncSetUp(self): 
#         self.sssc = asyncio.new_event_loop()
#         self.sssc.run_forever()
#         self.sssc.create_future()
#         self.sssc.run_in_executor(None, start_api(dask_scheduler_port=dask_scheduler_port))
#         # self.dask = Client()
#         # dask_scheduler_port = self.dask.scheduler.addr.split(":")[2]
#         dask_scheduler_port = 8786
#         # self.task = asyncio.create_task(start_api(dask_scheduler_port=dask_scheduler_port))
#         # self.task.
#         # self.sssc.run(None, )
#         time.sleep(3)
        

#     async def asyncTearDown(self) -> None:
#         # self.future.cancel()
#         close = self.dask.close()
#         if close is not None:
#             raise Exception('Dask cluster did not shut down correctly.')
        
#         for filename in os.listdir('cache'):
#             os.remove(f'cache/{filename}')

#     def test_run_0(self):
#         '''
#         Basic function.
#         '''
#         model = create_michaelis_menten()
#         server = ComputeServer('localhost')
#         sim = RemoteSimulation(model, server)
#         results = sim.run()
#         assert(results.data is not None)
#         assert 2 + 2 != 5
    #     local = True
    #     env = {}
    #     env['COVERAGE_PROCESS_START'] = ''
    #     if local:
    #         env['PYTHONPATH'] = '../env/lib/python3.11/site-packages'
    #     cls.api_server = subprocess.Popen(['/home/mdip/projects/StochSS-Compute/env/bin/coverage', 'run', '--source=../stochss_compute' '-a', '-m', 'stochss_compute.launch'], env=env)

    #     time.sleep(3)
    # @classmethod
    # def tearDownClass(cls) -> None:
    #     cls.api_server.terminate()
    #     cls.api_server.wait()
