import os
import subprocess
from stochss_compute.core.messages import SimulationRunRequest
from stochss_compute.server.api import _make_app
from stochss_compute.server.cache import Cache
from stochss_compute.server.run import RunHandler
# from distributed.utils_test import gen_cluster, client
from test.integration_tests.gillespy2_models import create_decay, create_dimerization, create_degradation
from tornado.httputil import HTTPServerRequest
from gillespy2 import Jsonify
import unittest

class MockHTTPConnObj:
    def set_close_callback(self, arg):
        pass
    def write_headers(self, bla, blah, blahh):
        pass
    def finish(self):
        pass

class MockRunHandler(RunHandler):
    cache_dir = 'cache/'
    host = 'localhost'
    port = 9999
    req = None
    _transforms = []
    
    def get_app(self):
        return _make_app(self.host, self.port, self.cache_dir)
    
    def __init__(self, request) -> None:
        uri = '/api/v2/simulation/gillespy2/run'
        sim_req = Jsonify.to_json(request)
        req = HTTPServerRequest(method='POST', uri=uri, body=sim_req, connection=MockHTTPConnObj())        
        super().__init__(self.get_app(), req, cache_dir=self.cache_dir, scheduler_address=None)

    def post(self):
        return super().post()

class TestRunHandler(unittest.IsolatedAsyncioTestCase):
    cache_dir = 'cache/'
    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.cache_dir):
            r_m = subprocess.Popen(['rm', '-r', cls.cache_dir])
            r_m.wait()
        return super().tearDownClass()

    async def test_run_0(self):
        sim_req = SimulationRunRequest(create_decay()).encode()
        handler = MockRunHandler(sim_req)
        await handler.post()

    async def test_run_1(self):
        sim_req = SimulationRunRequest(create_dimerization()).encode()
        handler = MockRunHandler(sim_req)
        await handler.post()

    async def test_run_ready(self):
        sim_req = SimulationRunRequest(create_decay()).encode()
        handler = MockRunHandler(sim_req)
        await handler.post()

    async def test_run_2_traj(self):
        model = create_degradation()
        sim_req = SimulationRunRequest(model)
        results = model.run()
        cache = Cache(self.cache_dir, sim_req.hash())
        cache.create()
        cache.save(results)
        sim_req2 = SimulationRunRequest(model, number_of_trajectories=2)
        handler = MockRunHandler(sim_req2.encode())
        await handler.post()

    async def test_run_solver_arg(self):
        model = create_degradation()
        sim_req = SimulationRunRequest(model, **{'solver': 'TauHybridSolver'})
        handler = MockRunHandler(sim_req.encode())
        await handler.post()

