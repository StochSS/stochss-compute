from tornado.web import RequestHandler
from tornado.ioloop import IOLoop
from stochss_compute.core.errors import RemoteSimulationError
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
        log_string = f'[Simulation Run Request] | Source: <{self.request.remote_ip}> | Simulation ID: <{sim_hash}> | '
        self.results_path = os.path.join(self.cache_dir, f'{sim_hash}.results')
        exists = os.path.exists(self.results_path)
        if not exists:
            open(self.results_path, 'w').close()
        empty = self._is_empty()
        if not empty:
            try:
                with open(self.results_path,'r') as results_json:
                    results = Results.from_json(results_json)
            except Exception:
                raise RemoteSimulationError('Malformed json')
            # Check the number of trajectories in the request, default 1
            n_traj = sim_request.kwargs.get('number_of_trajectories', 1)
            # Compare that to the number of cached trajectories
            n_cached_traj = len(results)
            if n_traj > n_cached_traj:
                sim_request.kwargs['number_of_trajectories'] -= n_cached_traj
                new_traj = sim_request.kwargs['number_of_trajectories']
                print(log_string + f'Partial cache. Running {new_traj} new trajectories.')
                future = self._submit(sim_request, sim_hash)
                await IOLoop.current().run_in_executor(None, self._cache, future)
            else:
                print(log_string + 'Returning cached results.')
                ret_traj = random.sample(results, n_traj)
                new_results = Results(ret_traj)
                new_results_json = new_results.to_json()
                sim_response = SimulationRunResponse(SimStatus.READY, results_id = sim_hash, results = new_results_json)
                self.write(sim_response._encode())
                self.finish()
        if empty:
            print(log_string + 'Results not cached. Running simulation.')
            self._return_pending(sim_hash)
            future = self._submit(sim_request, sim_hash)
            await IOLoop.current().run_in_executor(None, self._cache, future)
            
    def _is_empty(self):
        if os.path.exists(self.results_path):
            with open(self.results_path, 'r') as file:
                if file.read(1) == '':
                    file.seek(0)
                    return True
                else:
                    file.seek(0)
                    return False
        else:
            return True

    def _future(self, future_results: Future):
        results: Results = future_results.result()
        return results

    def _cache(self, future: Future):
        results = self._future(future)
        if self._is_empty():
            self._cache_results_empty(results)
        else:
            self._cache_add_results(results)

    def _cache_results_empty(self, results: Results):
        print(f'[Simulation Finished] | Simulation ID: <{self.results_path}> | Caching results.')
        with open(self.results_path, 'w') as file:
            file.write(results.to_json())

    def _cache_add_results(self, new_results: Results):
        print(f'[Simulation Finished] | Simulation ID: <{self.results_path}> | Caching results.')
        with open(self.results_path,'r') as file:
            old_results = Results.from_json(file.read())
        combined_results = new_results + old_results
        with open(self.results_path,'w') as file:
            file.write(combined_results.to_json())

    def _submit(self, sim_request, sim_hash):
        model = sim_request.model
        kwargs = sim_request.kwargs['kwargs']
        if "solver" in kwargs:
            from pydoc import locate
            kwargs["solver"] = locate(kwargs["solver"])

        # keep client open for now! close?
        client = Client(self.scheduler_address)
        future = client.submit(model.run, **kwargs, key=sim_hash)
        return future

    def _return_pending(self, results_id):
        sim_response = SimulationRunResponse(SimStatus.PENDING, results_id=results_id)
        self.write(sim_response._encode())
        self.finish()

    def _return_running(self, results_id):
        sim_response = SimulationRunResponse(SimStatus.RUNNING, results_id=results_id)
        self.write(sim_response._encode())
        self.finish()
