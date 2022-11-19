from tornado.web import RequestHandler
from tornado.ioloop import IOLoop
from stochss_compute.core.messages import SimStatus, SimulationRunRequest, SimulationRunResponse
from gillespy2.core import Results
from distributed import Client, Future
import os
import random

class RunHandler(RequestHandler):


    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def post(self):
        sim_request = SimulationRunRequest._parse(self.request.body)
        sim_hash = sim_request._hash()
        # write a blank file
            
        log_string = f'[Simulation Run Request] | Source: <{self.request.remote_ip}> | Simulation ID: <{sim_hash}> | '
        self.results_path = os.path.join(self.cache_dir, f'{sim_hash}.results')
        if os.path.exists(self.results_path):
            file = open(self.results_path, 'r')
            results_json = file.read()
            results = Results.from_json(results_json)
            file.close()

            n_traj = sim_request.kwargs.get('number_of_trajectories', 1)
            n_cached_traj = len(results)
            if sim_request.kwargs.get('seed', None) is None:
                if n_traj > n_cached_traj:
                    sim_request.kwargs['number_of_trajectories'] -= n_cached_traj
                    new_traj = sim_request.kwargs['number_of_trajectories']
                    print(log_string + f'Partial cache. Running {new_traj} new trajectories.')
                    future = self.process(sim_request, sim_hash)
                    await IOLoop.current().run_in_executor(None, self.cache_add_results, future)
                else:
                    print(log_string + 'Returning cached results.')
                    ret_traj = random.sample(results, n_traj)
                    new_results = Results(ret_traj)
                    new_results_json = new_results.to_json()
                    sim_response = SimulationRunResponse(SimStatus.READY, results_id = sim_hash, results = new_results_json)
                    self.write(sim_response._encode())
                    self.finish()
        else:
            print(log_string + 'Results not cached. Running simulation.')
            future = self.process(sim_request, sim_hash)
            await IOLoop.current().run_in_executor(None, self.cache_results, future)
    
    def cache_results(self, future_results: Future):
        results: Results = future_results.result()
        print(f'[Simulation Finished] | Simulation ID: <{future_results.key}> | Caching results.')
        file = open(self.results_path, 'x')
        file.write(results.to_json())
        file.close()

    def cache_add_results(self, future_results: Future):
        new_results: Results = future_results.result()
        print(f'[Simulation Finished] | Simulation ID: <{future_results.key}> | Caching results.')
        file = open(self.results_path,'r')
        old_results = Results.from_json(file.read())
        file.close()
        combined_results = new_results + old_results
        file = open(self.results_path,'w')
        file.write(combined_results.to_json())
        file.close()

    def process(self, sim_request, sim_hash):
        model = sim_request.model
        kwargs = sim_request.kwargs['kwargs']
        if "solver" in kwargs:
            from pydoc import locate
            kwargs["solver"] = locate(kwargs["solver"])

        client = Client(self.scheduler_address)
        future = client.submit(model.run, **kwargs, key=sim_hash)
        sim_response = SimulationRunResponse(SimStatus.PENDING, results_id=sim_hash)
        self.write(sim_response._encode())
        self.finish()
        return future
