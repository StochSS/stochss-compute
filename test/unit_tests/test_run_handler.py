# tests/test_submit.py

# import logging
# import os
# import subprocess
from tornado.testing import AsyncHTTPTestCase
# from distributed import Client, Future, Scheduler, Worker
# from gillespy2 import Jsonify
# from stochss_compute.core.messages import SimulationRunRequest, SimulationRunResponse

# from stochss_compute.server.api import _make_app
# from .gillespy2_models import create_decay
# from tornado.ioloop import IOLoop
# from distributed.utils_test import client
# class TestRunHandler(AsyncHTTPTestCase):
    # cache_dir = 'cache/'
    # host = 'localhost'
    # port = 9999
    # def tearDown(self) -> None:
    #     if os.path.exists(self.cache_dir):
    #         r_m = subprocess.Popen(['rm', '-r', self.cache_dir])
    #         r_m.wait()
    #     return super().tearDown()

    # def get_app(self):
    #     return _make_app(self.host, self.port, self.cache_dir)
    
from distributed.utils_test import gen_cluster, inc
from distributed import Client, Future, Scheduler, Worker
from stochss_compute.core.messages import SimulationRunRequest, SimulationRunResponse
from stochss_compute.server.api import _make_app
from test.unit_tests.gillespy2_models import create_decay

from gillespy2 import Jsonify

from test.unit_tests.mock_dask import mock_dask
class MockServer(AsyncHTTPTestCase):
    cache_dir = 'cache/'
    host = 'localhost'
    port = 9999
    def get_app(self):
        return _make_app(self.host, self.port, self.cache_dir)
    
    def test_run(self):
        dask = mock_dask()
        print(dask)
# @gen_cluster(client=True)
# async def mo(c, s, a, b):
#     '''
#     '''
#     print('========================')
#     print(c)
#     assert isinstance(c, Client)
#     assert isinstance(s, Scheduler)
#     assert isinstance(a, Worker)
#     assert isinstance(b, Worker)
#     print(f'*************{c.scheduler.address}')
#     mock_server = MockServer()
#     model = create_decay()
#     uri = '/api/v2/simulation/gillespy2/run'
#     request = Jsonify.to_json(SimulationRunRequest(model).encode())
#     response_raw = mock_server.get_http_client().fetch(uri, method='POST', body=request)
#     print(response_raw)
#     assert response_raw.code == 200
#     response = SimulationRunResponse.parse(response_raw.body)

        # future = c.submit(inc, 1)
        # assert isinstance(future, Future)
        # assert future.key in c.futures

        # # result = future.result()  # This synchronous API call would block
        # result = await future
        # assert result == 2

        # assert future.key in s.tasks
        # assert future.key in a.data or future.key in b.data