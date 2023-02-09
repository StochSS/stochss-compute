'''
test.unit_tests.test_results
'''
from gillespy2 import Jsonify
import json
import os
import subprocess
from tornado.testing import AsyncHTTPTestCase
from stochss_compute.core.messages import SourceIpRequest, SourceIpResponse
from stochss_compute.server.api import _make_app

class SourceIpHandlerTest(AsyncHTTPTestCase):
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

    def test_403(self):
        '''
        This uri should return a 403.
        '''
        # I think this is returning a 404 before getting to the handler.
        # not sure a way around it.
        uri = '/api/v2/cloud/sourceip'
        request = Jsonify.to_json(SourceIpRequest('4').encode())
        response_raw = self.fetch(uri, method='POST', body=request)
        assert response_raw.code == 403

    def test_127_0_0_1(self):
        '''

        '''
        uri = '/api/v2/cloud/sourceip'
        request = Jsonify.to_json(SourceIpRequest('4').encode())
        os.environ['CLOUD_LOCK'] = '4'
        response_raw = self.fetch(uri, method='POST', body=request)
        os.environ['CLOUD_LOCK'] = ''
        assert response_raw.code == 200
        response = SourceIpResponse.parse(response_raw.body)
        assert response.source_ip == '127.0.0.1'
