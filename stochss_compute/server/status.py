'''
stochss_compute.server.status
'''
from datetime import datetime
from distributed import Client
from tornado.web import RequestHandler
from stochss_compute.core.errors import RemoteSimulationError
from stochss_compute.core.messages import SimStatus, StatusResponse

from stochss_compute.server.cache import Cache

class StatusHandler(RequestHandler):
    '''
    Endpoint for requesting the status of a simulation.
    '''

    def initialize(self, scheduler_address, cache_dir):
        '''
        Sets the address to the Dask scheduler and the cache directory.
        
        :param scheduler_address: Scheduler address.
        :type scheduler_address: str

        :param cache_dir: Path to the cache.
        :type cache_dir: str
        '''
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def get(self, results_id = None, n_traj = None, task_id = None):
        '''
        Process GET request.

        :param results_id: Hash of the simulation. Required.
        :type results_id: str

        :param n_traj: Number of trajectories in the request. Default 1.
        :type n_traj: str
        
        :param task_id: ID of the running simulation. Required.
        :type task_id: str
        '''
        if None in (results_id, n_traj):
            raise RemoteSimulationError('Malformed request')
        self.results_id = results_id
        self.task_id = task_id
        n_traj = int(n_traj)
        cache = Cache(self.cache_dir, results_id)
        print(f'{datetime.now()} | <{self.request.remote_ip}> | \
              Status Request | <{results_id}> | Trajectories: {n_traj} | \
              Task ID: {task_id}' )
        msg = f'{datetime.now()} | <{results_id}> | <{task_id}> |Status: '
        exists = cache.exists()
        if exists:
            empty = cache.is_empty()
            if empty:
                if self.task_id is not None:
                    state, err = await self._check_with_scheduler()
                    print(msg+SimStatus.RUNNING.name+f' | Task: {state} | error: {err}')
                    if state == 'erred':
                        self._respond_error(err)
                    else:
                        self._respond_running(f'Scheduler task state: {state}')
                else:
                    print(msg+SimStatus.DOES_NOT_EXIST.name)
                    self._respond_dne()
            else:
                ready = cache.is_ready(n_traj)
                if ready:
                    print(msg+SimStatus.READY.name)
                    self._respond_ready()
                else:
                    if self.task_id is not None:
                        state, err = await self._check_with_scheduler()
                        print(msg+SimStatus.RUNNING.name+f' | Task: {state} | error: {err}')
                        if state == 'erred':
                            self._respond_error(err)
                        else:
                            self._respond_running(f'Scheduler task state: {state}')
                    else:
                        print(msg+SimStatus.DOES_NOT_EXIST.name)
                        self._respond_dne()
        else:
            print(msg+SimStatus.DOES_NOT_EXIST.name)
            self._respond_dne()


    def _respond_ready(self):
        status_response = StatusResponse(SimStatus.READY)
        self.write(status_response.encode())
        self.finish()

    def _respond_error(self, error_message):
        status_response = StatusResponse(SimStatus.ERROR, error_message)
        self.write(status_response.encode())
        self.finish()

    def _respond_dne(self):
        status_response = StatusResponse(SimStatus.DOES_NOT_EXIST, 'There is no record of that simulation.')
        self.write(status_response.encode())
        self.finish()

    def _respond_running(self, message):
        status_response = StatusResponse(SimStatus.RUNNING, message)
        self.write(status_response.encode())
        self.finish()

    async def _check_with_scheduler(self):
        '''
        Ask the scheduler for information about a task.
        '''
        client = Client(self.scheduler_address)

        # define function here so that it is pickle-able
        def scheduler_task_state(task_id, dask_scheduler=None):
            task = dask_scheduler.tasks.get(task_id)

            if task is None:
                return (None, None)
            if task.exception_text == "":
                return (task.state, None)
            return (task.state, task.exception_text)
        # Do not await. Reasons. It returns sync.
        ret = client.run_on_scheduler(scheduler_task_state, self.task_id)
        client.close()
        return ret
    