'''
test.unit_tests.test_results
'''
import os
import subprocess
from tornado.testing import AsyncHTTPTestCase
from stochss_compute.core.messages import SimulationRunRequest
from stochss_compute.server.api import _make_app
from stochss_compute.server.cache import Cache
from .gillespy2_models import create_michaelis_menten

class ResultsHandlerTest(AsyncHTTPTestCase):
    '''
    Test ResultsHandler class.
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
        uri = "/api/v2/simulation/gillespy2/asdf//results"
        response_raw = self.fetch(uri)
        assert response_raw.code == 404

    def test_is_ready(self):
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
        uri = f'/api/v2/simulation/gillespy2/{sim_hash}/1/results'
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        uri = f'/api/v2/simulation/gillespy2/{sim_hash}/2/results'
        response_raw = self.fetch(uri)
        assert response_raw.code == 404
