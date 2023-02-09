'''
test.unit_tests.test_results
'''
import os
import subprocess
from tornado.testing import AsyncHTTPTestCase
from stochss_compute.client.compute_server import ComputeServer
from stochss_compute.core.errors import RemoteSimulationError
from stochss_compute.core.messages import ResultsResponse, SimStatus, SimulationRunRequest, SimulationRunResponse, StatusResponse
from stochss_compute.core.remote_results import RemoteResults
from stochss_compute.server.api import _make_app
from stochss_compute.server.cache import Cache
from .gillespy2_models import create_michaelis_menten

class IsCachedHandlerTest(AsyncHTTPTestCase):
    '''
    Test IsCachedHandler class.
    '''
    cache_dir = 'cache/'
    host = 'localhost'
    port = 9999

    def tearDown(self) -> None:
        if os.path.exists(self.cache_dir):
            r_m = subprocess.Popen(['rm', '-r', self.cache_dir])
            r_m.wait()
        return super().tearDown()

    def get_app(self):
        return _make_app(self.host, self.port, self.cache_dir)

    def test_404(self):
        '''
        This uri should return a 404.
        '''
        # I think this is returning a 404 before getting to the handler.
        # not sure a way around it.
        uri = "/api/v2/cache/gillespy2///is_cached"
        response_raw = self.fetch(uri)
        assert response_raw.code == 404

    def test_dne_0(self):
        '''
        This uri should DNE
        '''
        uri = "/api/v2/cache/gillespy2/asdf/1/is_cached"
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        response = StatusResponse.parse(response_raw.body)
        assert response.status == SimStatus.DOES_NOT_EXIST

    def test_dne_1(self):
        '''
        This uri should return DNE.
        '''
        model = create_michaelis_menten()
        sim = SimulationRunRequest(model=model)
        sim_hash = sim.hash()
        cache = Cache(self.cache_dir, sim_hash)
        cache.create()
        uri = f'/api/v2/cache/gillespy2/{sim_hash}/1/is_cached'
        response_raw = self.fetch(uri)
        assert response_raw.code == 200

    def test_ready_not_ready(self):
        '''
        This uri should return a copy of these results
        '''
        model = create_michaelis_menten()
        results = model.run()
        sim = SimulationRunRequest(model=model)
        sim_hash = sim.hash()
        cache = Cache(self.cache_dir, sim_hash)
        cache.create()
        cache.save(results)
        uri = f'/api/v2/cache/gillespy2/{sim_hash}/1/is_cached'
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        response = StatusResponse.parse(response_raw.body)
        assert response.status == SimStatus.READY
        uri = f'/api/v2/cache/gillespy2/{sim_hash}/2/is_cached'
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        response = StatusResponse.parse(response_raw.body)
        assert response.status == SimStatus.DOES_NOT_EXIST
