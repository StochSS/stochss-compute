from datetime import datetime
from distributed import Client
from tornado.web import RequestHandler
from stochss_compute.core.errors import RemoteSimulationError
from stochss_compute.core.messages import SimStatus, StatusResponse

from stochss_compute.server.cache import Cache

class StatusHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def get(self, results_id = None, n_traj = None):
        if None in (results_id, n_traj):
            raise RemoteSimulationError('Malformed request')
        self.results_id = results_id
        n_traj = int(n_traj)
        cache = Cache(self.cache_dir, results_id)
        print(f'{datetime.now()} | <{self.request.remote_ip}> | Status Request | <{results_id}> | Trajectories: {n_traj}')
        msg = f'{datetime.now()} | <{results_id}> | Status: '
        exists = cache.exists()
        if exists:
            empty = cache.is_empty()
            if empty:
                state, err = self.check_with_scheduler()
                print(msg+SimStatus.RUNNING.name+f' | Task: {state} | error: {err}')
                if state == 'erred':
                    self._respond_error(err)
                else:
                    self._respond_running(f'Scheduler task state: {state}')
            else:
                ready = cache.is_ready(n_traj)
                if ready:
                    print(msg+SimStatus.READY.name)
                    self._respond_ready()
                else:
                    state, err = self.check_with_scheduler()
                    print(msg+SimStatus.RUNNING.name+f' | Task: {state} | error: {err}')
                    if state == 'erred':
                        self._respond_error(err)
                    else:
                        self._respond_running(f'Scheduler task state: {state}')
        else:
            print(msg+SimStatus.DOES_NOT_EXIST.name)
            self._respond_DNE()


    def _respond_ready(self):
        status_response = StatusResponse(SimStatus.READY)
        self.write(status_response._encode())
        self.finish()
    
    def _respond_error(self, error_message):
        status_response = StatusResponse(SimStatus.ERROR, error_message)
        self.write(status_response._encode())
        self.finish()

    def _respond_DNE(self):
        status_response = StatusResponse(SimStatus.DOES_NOT_EXIST, 'There is no record of that simulation.')
        self.write(status_response._encode())
        self.finish()

    def _respond_running(self, message):
        status_response = StatusResponse(SimStatus.RUNNING, message)
        self.write(status_response._encode())
        self.finish()

    def check_with_scheduler(self):
        client = Client(self.scheduler_address)

        # define function here so that it is pickle-able
        def scheduler_task_state(dask_scheduler, results_id):
            task = dask_scheduler.tasks.get(results_id)

            if task is None:
                return (None, None)
            if task.exception_text == "":
                 return (task.state, None)
            return (task.state, task.exception_text)
        
        return client.run_on_scheduler(scheduler_task_state, results_id=self.results_id)