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
        print(f'{datetime.now()} | Status Request | Source: <{self.request.remote_ip}> | <{results_id}> | Trajectories: {n_traj}')
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
        status_response = StatusResponse(SimStatus.DOES_NOT_EXIST, 'There is no record of that simulation')
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





    
        # if state == 'released':
        #     # Not on disk, but either just about to start, or just finished
        #     sleep(1)
        #     # give it a sec and try again
        #     state = self.check_with_scheduler()
        #     if state == 'released':
        #         if self.is_in_cache():
        #             # Turns out it just finished
        #             self.respond_ready()
        #             return
        #         # Either it's lost or was never sent
        #         self.error_message = "Cannot locate simulation. It is not on disk and does not appear to be running."
        #         self.respond_error()
        #         return

        # if state == 'processing':
        #     self.respond_running()
        #     return

        # if state == 'memory':
        #     self.respond_pending()
        #     return

        # if state == 'forgotten':
        #     # Either it JUST finished (unlikely)
        #     sleep(1)
        #     if self.is_in_cache():
        #         self.respond_ready()
        #         return
        #     # Or something seriously messed up (but it was definitely sent)
        #     else:
        #         self.error_message = "If this is your error message please file a bug report on github. Sorry."
        #         self.respond_error()
        #         return
        
        # if state is None:
        #     # The scheduler doesn't know, just to be sure, check if there is a future.
        #     client = Client(self.scheduler_address)
        #     future = client.futures.get(results_id)
        #     if future is None:
        #         # Don't know about anything!
        #         self.respond_DNE()
        #         return
        #     if future.done():
        #         # Apparently, it just finished so maybe go back and check disk once more?
        #         sleep(1)
        #         if self.is_in_cache():
        #             self.respond_ready()
        #             return
        #         # Something broke.
        #         self.error_message = "The simulation has finished but cannot locate results. If this is your error message please file a bug report on github. Sorry."
        #         self.respond_error()
        #         return
                
        
        # if state == 'erred':
        #     # error message is already set.
        #     self.respond_error(error_message)
        #     return

        # if state == 'waiting' or state == 'no-worker' or state == 'queued':
        #     self.respond_pending()
        #     return

        # self.respond_DNE()
        # return


