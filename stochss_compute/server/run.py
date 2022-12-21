from tornado.web import RequestHandler
from tornado.ioloop import IOLoop
from stochss_compute.core.errors import RemoteSimulationError
from stochss_compute.core.messages import SimStatus, SimulationRunRequest, SimulationRunResponse
from stochss_compute.server.cache import Cache
from gillespy2.core import Results
from distributed import Client, Future
import os
import random
from datetime import datetime


class RunHandler(RequestHandler):


    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def post(self):
        sim_request = SimulationRunRequest._parse(self.request.body)
        sim_hash = sim_request._hash()
        log_string = f'{datetime.now()} | Simulation Run Request | <{self.request.remote_ip}> | <{sim_hash}> | '
        cache = Cache(self.cache_dir, sim_hash)
        empty = cache.is_empty()
        if not empty:
            # Check the number of trajectories in the request, default 1
            n_traj = sim_request.kwargs.get('number_of_trajectories', 1)
            # Compare that to the number of cached trajectories
            trajectories_needed =  cache.n_traj_needed(n_traj)
            if trajectories_needed > 0:
                sim_request.kwargs['number_of_trajectories'] = trajectories_needed
                print(log_string + f'Partial cache. Running {trajectories_needed} new trajectories.')
                self._return_running(sim_hash)
                future = self._submit(sim_request, sim_hash)
                await IOLoop.current().run_in_executor(None, self._cache, future)
            else:
                print(log_string + 'Returning cached results.')
                results = cache.get()
                ret_traj = random.sample(results, n_traj)
                new_results = Results(ret_traj)
                new_results_json = new_results.to_json()
                sim_response = SimulationRunResponse(SimStatus.READY, results_id = sim_hash, results = new_results_json)
                self.write(sim_response._encode())
                self.finish()
        if empty:
            cache.create()
            print(log_string + 'Results not cached. Running simulation.')
            self._return_running(sim_hash)
            future = self._submit(sim_request, sim_hash)
            await IOLoop.current().run_in_executor(None, self._cache, future)

    def _cache(self, future: Future):
        results = future.result()
        cache = Cache(self.cache_dir, future.key)
        cache.save(results)

    def _submit(self, sim_request, sim_hash):
        model = sim_request.model
        kwargs = sim_request.kwargs

        if "solver" in kwargs:
            from pydoc import locate
            kwargs["solver"] = locate(kwargs["solver"])

        # keep client open for now! close?
        client = Client(self.scheduler_address)
        future = client.submit(model.run, **kwargs, key=sim_hash)
        return future

    def _return_running(self, results_id):
        sim_response = SimulationRunResponse(SimStatus.RUNNING, results_id=results_id)
        self.write(sim_response._encode())
        self.finish()
