import os
from tornado.web import RequestHandler
from stochss_compute.core.messages import SimStatus, StatusResponse
from distributed import Client
from distributed.scheduler import TaskState

class StatusHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    async def get(self, results_id = None):
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

        def scheduler_job_state(dask_scheduler, results_id) -> TaskState:
            # still need to handle exception if there is one
            task = dask_scheduler.tasks.get(results_id)
            if task is None:
                return None
            return task.state



        state = client.run_on_scheduler(scheduler_job_state, results_id=results_id)
        # task = client.cluster.scheduler.tasks.get(results_id)
        # print(client.cluster.scheduler)
        if state is None or state == 'forgotten' or state == 'released':
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
        
        sim_status = status_mapping[state]
        
        if state == 'erred':
            error_message = exception_text
        elif state == 'memory' or state == 'forgotten':
            error_message = 'Unknown Error.'
        else:
            error_message = ''
        
        status_response = StatusResponse(sim_status, error_message)
        self.write(status_response.encode())
        self.finish()
