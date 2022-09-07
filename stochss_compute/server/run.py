from tornado.web import RequestHandler
from tornado.ioloop import IOLoop
from stochss_compute.core.messages import SimStatus, SimulationRunRequest, SimulationRunResponse
from gillespy2.core import Results
from distributed import Client, Future
import os

class RunHandler(RequestHandler):


    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def post(self):
        sim_request = SimulationRunRequest.parse(self.request.body)
        sim_hash = sim_request.hash()
        log_string = f'[Simulation Run Request] | Source: <{self.request.remote_ip}> | Simulation ID: <{sim_hash}> | '
        self.results_path = os.path.join(self.cache_dir, f'{sim_hash}.results')
        if os.path.exists(self.results_path):
            print(log_string + 'Returning cached results.')
            file = open(self.results_path, 'r')
            results = file.read()
            file.close()
            sim_response = SimulationRunResponse(SimStatus.READY, results_id = sim_hash, results = results)
            self.write(sim_response.encode())
        else:
            print(log_string + 'Results not cached. Running simulation.')
            model = sim_request.model
            kwargs = sim_request.kwargs
            if "solver" in kwargs:
                from pydoc import locate
                kwargs["solver"] = locate(kwargs["solver"])

            client = Client(self.scheduler_address)
            future = client.submit(model.run, key=sim_hash)
            sim_response = SimulationRunResponse(SimStatus.PENDING, results_id=sim_hash)
            self.write(sim_response.encode())
            self.finish()
            await IOLoop.current().run_in_executor(None, self.cache_results, future)
    
    def cache_results(self, future_results: Future):
        results: Results = future_results.result()
        print(f'[Simulation Finished] | Simulation ID: <{future_results.key}> | Caching results.')
        file = open(self.results_path, 'x')
        file.write(results.to_json())
        file.close()
