import hashlib
from time import sleep
from tornado.web import RequestHandler
from tornado.escape import json_decode, json_encode
import json
from gillespy2.core import Model
from messages import SimulationRunRequest
from gillespy2.core import Results
from distributed import Client, Future
from distributed.scheduler import TaskState
import os
import asyncio

class RunHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir
        self.running = {}

    async def post(self):
        sim_request = SimulationRunRequest.parse(self.request.body)
        print(sim_request.model)
        print(sim_request.kwargs)
        model: Model = Model.from_json(model_string)
        kwargs: dict = json_decode(kwargs_string)
        hashable = f'{model_string}{kwargs_string}'
        print(f'>>>>>>>HASHABLE:{hashable}')
        simulation_hash = hashlib.md5(str.encode(hashable)).hexdigest()
        print(f'>>>>>>>HASH: {simulation_hash}')
        
        self.results_path = os.path.join(self.cache_dir, f'{simulation_hash}.results')
        if os.path.exists(self.results_path):

            file = open(self.results_path, 'r')
            results = file.read()
            self.write(results)
        else:
            
            if "solver" in kwargs:
                from pydoc import locate
                kwargs["solver"] = locate(kwargs["solver"])

            client = Client(self.scheduler_address)
            if simulation_hash in self.running.keys():
                # fetch status by key
                key = self.running[simulation_hash]
                task : TaskState = client.cluster.scheduler.tasks[key]
                self.write(task.state)
            print(client)
            future: Future = client.submit(model.run)
            self.write(future.key)
            await self.cache_results(future)
        self.finish()
    
    def cache_results(self, future_results: Future):
        results: Results = future_results.result()
        file = open(self.results_path, 'x')
        file.write(results.to_json())
        file.close()

        
# class ResultsHandler(RequestHandler):
#     def 
        
        
