'''
test.unit_tests.test_launch
'''
import os
import subprocess
from test.unit_tests.gillespy2_models import create_michaelis_menten
from tornado.testing import AsyncHTTPTestCase
from stochss_compute.core.messages import SimStatus, SimulationRunRequest, StatusResponse
from stochss_compute.server.api import _make_app
from stochss_compute.server.cache import Cache


class StatusTest(AsyncHTTPTestCase):
    '''
    Test StatusHandler class.
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

    def test_status_dne_0(self):
        '''
        This uri should return SimStatus.DOES_NOT_EXIST
        '''
        uri = "/api/v2/simulation/gillespy2/test/dne/1/dne/status"
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        status_response = StatusResponse.parse(response_raw.body)
        assert status_response.status == SimStatus.DOES_NOT_EXIST

    def test_status_dne_1(self):
        '''
        This uri should return SimStatus.DOES_NOT_EXIST
        '''
        cache = Cache(cache_dir=self.cache_dir,results_id='test')
        cache.create()
        uri = "/api/v2/simulation/gillespy2/test/1//status"
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        status_response = StatusResponse.parse(response_raw.body)
        assert status_response.status == SimStatus.DOES_NOT_EXIST

    def test_status_dne_2(self):
        '''
        This uri should return SimStatus.DOES_NOT_EXIST
        '''
        cache = Cache(cache_dir=self.cache_dir,results_id='test')
        cache.create()
        uri = "/api/v2/simulation/gillespy2/test/1//status"
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        status_response = StatusResponse.parse(response_raw.body)
        assert status_response.status == SimStatus.DOES_NOT_EXIST

    def test_status_dne_3(self):
        '''
        This uri should return SimStatus.DOES_NOT_EXIST
        '''
        cache = Cache(cache_dir=self.cache_dir,results_id='test')
        cache.create()
        with open(cache.results_path, 'w+', encoding='utf-8') as file:
            file.write('test')
        uri = "/api/v2/simulation/gillespy2/test/1//status"
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        status_response = StatusResponse.parse(response_raw.body)
        assert status_response.status == SimStatus.DOES_NOT_EXIST

    def test_status_404(self):
        '''
        This uri should return a 404.
        '''
        uri = "/api/v2/simulation/gillespy2////status"
        response_raw = self.fetch(uri)
        assert response_raw.code == 404

    def test_status_ready(self):
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
        uri = f'/api/v2/simulation/gillespy2/{sim_hash}/1//status'
        response_raw = self.fetch(uri)
        assert response_raw.code == 200
        status_response = StatusResponse.parse(response_raw.body)
        assert status_response.status == SimStatus.READY

