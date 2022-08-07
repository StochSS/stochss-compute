import hashlib
from time import sleep
from tornado.web import RequestHandler
from tornado.escape import json_decode
import json
from gillespy2.core import Model
from messages import SimulationRunRequest
from gillespy2.core import jsonify
from distributed import Client
import os

class RunHandler(RequestHandler):

    def initialize(self, scheduler_address):
        self.scheduler_address = scheduler_address

    def post(self):
        request_dict = json_decode(self.request.body)
        model_string = request_dict['model']
        algorithm = request_dict['algorithm']
        model: Model = Model.from_json(model_string)
        simulation_hash = hashlib.md5(str.encode(f'{model_string}{algorithm}')).hexdigest()
        results_filename = f'{simulation_hash}.results'
        if os.path.exists(results_filename):
            file = open(results_filename, 'r')
            results = file.read()
            self.write(results)
        else:
            client = Client(self.scheduler_address)
            print(client)
            future = client.submit(Model.run, [model])
            print(future)
        # else
        # dask.submit

        

# class ResultsHandler(RequestHandler):
#     def 
        
        
