import hashlib
from time import sleep
from tornado.web import RequestHandler
from tornado.escape import json_decode, json_encode
import json
from gillespy2.core import Model
from stochss_compute.core.messages import SimStatus, SimulationRunRequest, SimulationRunResponse
from gillespy2.core import Results
from distributed import Client, Future
from distributed.scheduler import TaskState
import os
import asyncio

class RunHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def post(self):
        sim_request = SimulationRunRequest.parse(self.request.body)
        sim_hash = sim_request.hash()
        print(f'>>>>>>>HASH: {sim_hash}')
        
        self.results_path = os.path.join(self.cache_dir, f'{sim_hash}.results')
        if os.path.exists(self.results_path):

            file = open(self.results_path, 'r')
            results = file.read()
            sim_response = SimulationRunResponse(SimStatus.READY, results_id = sim_hash, results = results)
            self.write(sim_response.encode())
        else:
            model = sim_request.model
            kwargs = sim_request.kwargs
            if "solver" in kwargs:
                from pydoc import locate
                kwargs["solver"] = locate(kwargs["solver"])

            client = Client(self.scheduler_address)
            future: Future = client.submit(model.run, key=sim_hash)
            sim_response = SimulationRunResponse(SimStatus.PENDING, results_id=sim_hash)
            self.write(sim_response.encode())
            self.finish()
            self.cache_results(future)
    
    async def cache_results(self, future_results: Future):
        results: Results = yield future_results.result()
        print('done')
        file = open(self.results_path, 'x')
        file.write(results.to_json())
        file.close()

        
# class ResultsHandler(RequestHandler):
#     def 
        
        
