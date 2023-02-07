from unittest import IsolatedAsyncioTestCase
from tornado.httpclient import AsyncHTTPClient
import tornado
from stochss_compute.server.api import _make_app
import subprocess, os
class TestRunHandler(IsolatedAsyncioTestCase):

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

    
    @tornado.testing.gen_test
    def test_run(self):
        uri = '/api/v2/simulation/gillespy2/run'
        client = AsyncHTTPClient()
        response = yield client.fetch(f'http://{self.host}:{self.port}/{uri}')
        print(response)

