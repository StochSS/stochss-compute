import os
from tornado.web import RequestHandler
from stochss_compute.core.messages import SimStatus, StatusResponse
from distributed import Client

class StatusHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def post(self, results_id = None):
        if results_id is None:
            # This should not happen
            raise Exception('Malformed request')
        # what
        client = Client(self.scheduler_address)
        future = client.futures.get(results_id)

        print(f'[Stop Request] | Source: <{self.request.remote_ip}> | Results ID: <{results_id}>')

        """ 
        People could do a 'DDos' by calling stop
         """


