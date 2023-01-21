'''
stochss_compute.server.is_cached
'''
from datetime import datetime
from tornado.web import RequestHandler
from stochss_compute.core.errors import RemoteSimulationError
from stochss_compute.core.messages import SimStatus, StatusResponse
from stochss_compute.server.cache import Cache

class IsCachedHandler(RequestHandler):
    '''
    Endpoint that will determine if a particular simulation exists in the cache.
    '''
    def initialize(self, cache_dir):
        '''
        Set variables.
        '''
        self.cache_dir = cache_dir

    async def get(self, results_id = None, n_traj = None):
        '''
        Process GET request.

        :param results_id: Hash of the simulation.
        :param n_traj: Number of trajectories to check for.
        '''
        if None in (results_id, n_traj):
            raise RemoteSimulationError('Malformed request')
        n_traj = int(n_traj)
        cache = Cache(self.cache_dir, results_id)
        print(f'''
{datetime.now()} |
 Source: <{self.request.remote_ip}> |
 Cache Check |
 <{results_id}> |
 Trajectories: {n_traj} ''')
        msg = f'{datetime.now()} | <{results_id}> | Trajectories: {n_traj} | Status: '
        exists = cache.exists()
        if exists:
            empty = cache.is_empty()
            if empty:
                print(msg+SimStatus.DOES_NOT_EXIST.name)
                self._respond_dne('That simulation is not currently cached.')
            else:
                ready = cache.is_ready(n_traj)
                if ready:
                    print(msg+SimStatus.READY.name)
                    self._respond_ready()
                else:
                    print(msg+SimStatus.DOES_NOT_EXIST.name)
                    self._respond_dne(f'Not enough trajectories in cache. \
                                      Requested: {n_traj}, Available: {cache.n_traj_in_cache()}')
        else:
            print(msg+SimStatus.DOES_NOT_EXIST.name)
            self._respond_dne('There is no record of that simulation')

    def _respond_ready(self):
        status_response = StatusResponse(SimStatus.READY)
        self.write(status_response.encode())
        self.finish()

    def _respond_dne(self, msg):
        status_response = StatusResponse(SimStatus.DOES_NOT_EXIST, msg)
        self.write(status_response.encode())
        self.finish()
