import os
from tornado.web import RequestHandler
from stochss_compute.core.messages import SimStatus, StatusResponse
from distributed import Client
from distributed.scheduler import TaskState

class StatusHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    def get(self, results_id = None):
        if results_id is None:
            raise Exception('Malformed request')
        print(f'>>>>>>>>>>>ID:{results_id}')
        self.results_path = os.path.join(self.cache_dir, f'{results_id}.results')
        if os.path.exists(self.results_path):
            status_response = StatusResponse(SimStatus.READY)
            self.write(status_response.encode())
            self.finish()
            return
        
        client = Client(self.scheduler_address)
        task = client.scheduler.tasks.get(results_id)
        
        if task is None or task.state == 'forgotten' or task.state == 'released':
            future = client.futures.get(results_id)
            if future is None or future.done():
                status_response = StatusResponse(SimStatus.ERROR, 'Unknown Error.')
                self.write(status_response.encode())
                self.finish()
                return
                
        status_mapping = {
            "released": SimStatus.PENDING,
            "waiting": SimStatus.PENDING, 
            "no-worker": SimStatus.PENDING,
            "processing": SimStatus.RUNNING,
            "memory": SimStatus.ERROR, 
            "erred": SimStatus.ERROR, 
            "forgotten": SimStatus.ERROR
        }
        
        sim_status = status_mapping[task.state]
        
        if task.state == 'erred':
            error_message = task.exception_text
        elif task.state == 'memory' or task.state == 'forgotten':
            error_message = 'Unknown Error.'
        else:
            error_message = ''
        
        status_response = StatusResponse(sim_status, error_message)
        self.write(status_response.encode())
        self.finish()