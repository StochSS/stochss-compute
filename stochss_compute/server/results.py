import os
from tornado.web import RequestHandler
from stochss_compute.core.messages import ResultsResponse

class ResultsHandler(RequestHandler):

    def initialize(self, cache_dir):
        self.cache_dir = cache_dir

    async def get(self, results_id = None):
        if results_id is None:
            raise Exception('Malformed request')
        print(f'[Results Request] | Source: <{self.request.remote_ip}> | ID: <{results_id}>')
        results_path = os.path.join(self.cache_dir, f'{results_id}.results')
        if os.path.exists(results_path):
            file = open(results_path, 'r')
            results = file.read()
            file.close()
            results_response = ResultsResponse(results)
            self.write(results_response.encode())
        else:
            # This should not happen!
            self.set_status(404, f'Results "{results_id}" not found.')
        self.finish()
