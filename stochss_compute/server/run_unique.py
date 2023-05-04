'''
stochss_compute.server.run
'''
# StochSS-Compute is a tool for running and caching GillesPy2 simulations remotely.
# Copyright (C) 2019-2023 GillesPy2 and StochSS developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import random
from datetime import datetime
from secrets import token_hex

from tornado.web import RequestHandler
from tornado.ioloop import IOLoop
from distributed import Client, Future
from gillespy2.core import Results
from stochss_compute.core.messages.status import SimStatus
from stochss_compute.core.exceptions import PRNGCollision
from stochss_compute.core.messages.simulation_run_unique import SimulationRunUniqueRequest, SimulationRunUniqueResponse
from stochss_compute.server.cache import Cache


class SimulationRunUniqueHandler(RequestHandler):
    '''
    Endpoint for running Gillespy2 simulations.
    '''

    def __init__(self, application, request, **kwargs):
        self.scheduler_address = None
        self.cache_dir = None
        self.unique_key = None
        super().__init__(application, request, **kwargs)

    def data_received(self, chunk: bytes):
        raise NotImplementedError()
    
    def initialize(self, scheduler_address, cache_dir):
        '''
        Sets the address to the Dask scheduler and the cache directory.

        :param scheduler_address: Scheduler address.
        :type scheduler_address: str

        :param cache_dir: Path to the cache.
        :type cache_dir: str
        '''
        self.scheduler_address = scheduler_address
        while cache_dir.endswith('/'):
            cache_dir = cache_dir[:-1]
        self.cache_dir = cache_dir + '/unique/'

    async def post(self):
        '''
        Process simulation run unique request.
        '''
        sim_request = SimulationRunUniqueRequest.parse(self.request.body)
        unique_key = sim_request.unique_key
        log_string = f'{datetime.now()} | <{self.request.remote_ip}> | Simulation Run Unique Request | <{unique_key}> | '
        cache = Cache(self.cache_dir, unique_key)
        if cache.exists():
            raise PRNGCollision('Try again with a different key, because that one is taken.')
        cache.create()
        client = Client(self.scheduler_address)
        future = self._submit(sim_request, client)
        self._return_running(unique_key)
        IOLoop.current().run_in_executor(None, self._cache, sim_hash, future, client)

    def _cache(self, sim_hash, future: Future, client: Client):
        results = future.result()
        client.close()
        cache = Cache(self.cache_dir, sim_hash)
        cache.save(results)

    def _submit(self, sim_request, client: Client):
        model = sim_request.model
        kwargs = sim_request.kwargs
        unique_key = sim_request.unique_key
        if "solver" in kwargs:
            from pydoc import locate
            kwargs["solver"] = locate(kwargs["solver"])

        # keep client open for now! close?
        future = client.submit(model.run, **kwargs, key=unique_key)
        return future

    def _return_running(self, results_id, task_id):
        sim_response = SimulationRunResponse(SimStatus.RUNNING, results_id=results_id, task_id=task_id)
        self.write(sim_response.encode())
        self.finish()
