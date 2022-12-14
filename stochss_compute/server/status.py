import os
from time import sleep
from tornado.web import RequestHandler
from stochss_compute.core.messages import SimStatus, StatusResponse
from distributed import Client

class StatusHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir


    async def get(self, results_id = None):
        self.results_id = results_id
        if results_id is None:
            raise Exception('Malformed request')

        print(f'[Status Request] | Source: <{self.request.remote_ip}> | Results ID: <{results_id}>')
        self.results_path = os.path.join(self.cache_dir, f'{results_id}.results')
        self.error_message = None
        # First check if results are on disk
        if self.is_in_cache():
            self.respond_ready()
            return

        task_dict = self.check_with_scheduler()

        if task_dict is None:
            state = None
        else:
            state = task_dict['state']
        if state == 'erred':
            error_message = task_dict['exception_text']
    
        if state == 'released':
            # Not on disk, but either just about to start, or just finished
            sleep(1)
            # give it a sec and try again
            state = self.check_with_scheduler()
            if state == 'released':
                if self.is_in_cache():
                    # Turns out it just finished
                    self.respond_ready()
                    return
                # Either it's lost or was never sent
                self.error_message = "Cannot locate simulation. It is not on disk and does not appear to be running."
                self.respond_error()
                return

        if state == 'processing':
            self.respond_running()
            return

        if state == 'memory':
            self.respond_pending()
            return

        if state == 'forgotten':
            # Either it JUST finished (unlikely)
            sleep(1)
            if self.is_in_cache():
                self.respond_ready()
                return
            # Or something seriously messed up (but it was definitely sent)
            else:
                self.error_message = "If this is your error message please file a bug report on github. Sorry."
                self.respond_error()
                return
        
        if state is None:
            # The scheduler doesn't know, just to be sure, check if there is a future.
            client = Client(self.scheduler_address)
            future = client.futures.get(results_id)
            if future is None:
                # Don't know about anything!
                self.respond_DNE()
                return
            if future.done():
                # Apparently, it just finished so maybe go back and check disk once more?
                sleep(1)
                if self.is_in_cache():
                    self.respond_ready()
                    return
                # Something broke.
                self.error_message = "The simulation has finished but cannot locate results. If this is your error message please file a bug report on github. Sorry."
                self.respond_error()
                return
                
        
        if state == 'erred':
            # error message is already set.
            self.respond_error(error_message)
            return

        if state == 'waiting' or state == 'no-worker' or state == 'queued':
            self.respond_pending()
            return

        self.respond_DNE()
        return




    def respond_ready(self):
        status_response = StatusResponse(SimStatus.READY)
        self.write(status_response._encode())
        self.finish()

    def respond_pending(self):
        status_response = StatusResponse(SimStatus.PENDING)
        self.write(status_response._encode())
        self.finish()
    
    def respond_error(self, error_message):
        status_response = StatusResponse(SimStatus.ERROR, error_message)
        self.write(status_response._encode())
        self.finish()

    def respond_DNE(self):
        status_response = StatusResponse(SimStatus.DOES_NOT_EXIST)
        self.write(status_response._encode())
        self.finish()


    def respond_running(self):
        status_response = StatusResponse(SimStatus.RUNNING)
        self.write(status_response._encode())
        self.finish()

    def is_in_cache(self):
        return os.path.exists(self.results_path)

    def check_with_scheduler(self):
        client = Client(self.scheduler_address)

        # define function here so that it is pickle-able
        def scheduler_task_state(dask_scheduler, results_id):
            task = dask_scheduler.tasks.get(results_id)

            if task is None:
                return None
            return {
                'state': task.state,
                'exception_text': task.exception_text,
            }
        
        # results are not on disk, so ask the scheduler about the task
        task_dict = client.run_on_scheduler(scheduler_task_state, results_id=self.results_id)
        return task_dict


