from datetime import datetime
from tornado.web import RequestHandler
from stochss_compute.core.errors import RemoteSimulationError
from stochss_compute.core.messages import SimStatus, StatusResponse
from stochss_compute.server.cache import Cache

# TODO could possibly respond with number of trajectories in cache 
class IsCachedHandler(RequestHandler):

    def initialize(self, cache_dir):
        self.cache_dir = cache_dir

    async def get(self, results_id = None, n_traj = None):
        if None in (results_id, n_traj):
            raise RemoteSimulationError('Malformed request')
        n_traj = int(n_traj)
        cache = Cache(self.cache_dir, results_id)
        print(f'''
{datetime.now()} |
 Cache Check |
 Source: <{self.request.remote_ip}> |
 <{results_id}> |
 Trajectories: {n_traj} ''')
        msg = f'{datetime.now()} | <{results_id}> | Trajectories: {n_traj} | Status: '
        exists = cache.exists()
        if exists:
            empty = cache.is_empty()
            if empty:
                print(msg+SimStatus.DOES_NOT_EXIST.name)
                self._respond_DNE()
            else:
                ready = cache.is_ready(n_traj)
                if ready:
                    print(msg+SimStatus.READY.name)
                    self._respond_ready()
                else:
                    print(msg+SimStatus.DOES_NOT_EXIST.name)
                    self._respond_DNE()
        else:
            print(msg+SimStatus.DOES_NOT_EXIST.name)
            self._respond_DNE()

    def _respond_ready(self):
        status_response = StatusResponse(SimStatus.READY)
        self.write(status_response._encode())
        self.finish()

    def _respond_DNE(self):
        status_response = StatusResponse(SimStatus.DOES_NOT_EXIST, 'There is no record of that simulation')
        self.write(status_response._encode())
        self.finish()