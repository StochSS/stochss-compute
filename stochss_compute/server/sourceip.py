'''
stochss_compute.server.sourceip
'''
import os
from tornado.web import RequestHandler
from stochss_compute.core.messages import SourceIpRequest, SourceIpResponse

class SourceIpHandler(RequestHandler):
    '''
    Responds with the IP address associated with the request.
    Used only by cloud api.
    '''

    def post(self):
        '''
        Process POST request.
        
        :returns: request.remote_ip
        '''
        source_ip = self.request.remote_ip
        print(f'[SourceIp Request] | Source: <{source_ip}>')
        source_ip_request = SourceIpRequest.parse(self.request.body)
        # could possibly also check just to see if request is valid?
        if source_ip_request.cloud_key == os.environ.get('CLOUD_LOCK'):
            source_ip_response = SourceIpResponse(source_ip=source_ip)
            self.write(source_ip_response.encode())
        else:
            self.set_status(403, 'Access denied.')
        self.finish()
