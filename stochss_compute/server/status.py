from tornado.web import RequestHandler

class StatusHandler(RequestHandler):

    def initialize(self, scheduler_address, cache_dir):
        self.scheduler_address = scheduler_address
        self.cache_dir = cache_dir

    def get(self, results_id = None):
        print(f'>>>>>>>>>>>ID:{results_id}')
            
            # client = Client(self.scheduler_address)
            # if simulation_hash in self.running.keys():
            #     # fetch status by key
            #     key = self.running[simulation_hash]
            #     task : TaskState = client.cluster.scheduler.tasks[key]
            #     self.write(task.state)
