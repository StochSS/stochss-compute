import hashlib
from tornado.web import RequestHandler
from tornado.escape import json_decode
from gillespy2.core import Model
from stochss_compute.core.messages import SimulationRunRequest
from gillespy2.core import Results
from distributed import Client, Future
from distributed.scheduler import TaskState
import os

class RunHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir
        self.running = {}

    def post(self):
        request_dict = json_decode(self.request.body)
        model_string = request_dict['model']
        algorithm = request_dict['algorithm']
        model: Model = Model.from_json(model_string)
        simulation_hash = hashlib.md5(str.encode(f'{model_string}{algorithm}')).hexdigest()
        
        self.results_path = os.path.join(self.cache_dir, f'{simulation_hash}.results')
        if os.path.exists(self.results_path):
            file = open(self.results_path, 'r')
            results = file.read()
            self.write(results)
        else:
            
            client = Client(self.scheduler_address)
            if simulation_hash in self.running.keys():
                # fetch status by key
                key = self.running[simulation_hash]
                task : TaskState = client.cluster.scheduler.tasks[key]
                self.write(task.state)
            print(client)
            future: Future = client.submit(model.run)
            self.write(future.key)
            future.add_done_callback(self.cache_results)
        # else
        # dask.submit
    
    def cache_results(self, future_results: Future):
        results: Results = future_results.result()
        file = open(self.results_path, 'x')
        file.write(results.to_json())
        file.close()

        

# class ResultsHandler(RequestHandler):
#     def 
        
        
