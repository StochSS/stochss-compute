from stochss_compute.server.api import start_api
from argparse import ArgumentParser, Namespace
import asyncio
from distributed import LocalCluster

def launch_server():
    def parse_args() -> Namespace:
        desc = '''
            StochSS-Compute is a server and cache that anonymizes StochSS simulation data.
        '''
        parser = ArgumentParser(description=desc, add_help=True, conflict_handler='resolve')

        server = parser.add_argument_group('Server')
        # Will have to make sure this works in docker
        # server.add_argument("-h", "--host", default='127.0.0.1', required=False,
        #                     help="The host to use for the flask server. Defaults to localhost.")
        server.add_argument("-p", "--port", default=29681, type=int, required=False,
                            help="The port to use for the server. Defaults to 29681.")

        cache = parser.add_argument_group('Cache')
        cache.add_argument('-c', '--cache', default='cache/', required=False, help='Path to use for the cache.')

        dask = parser.add_argument_group('Dask')
        dask.add_argument("-H", "--dask-host", default='localhost', required=False,
                            help="The host to use for the dask scheduler. Defaults to localhost.")
        dask.add_argument("-P", "--dask-scheduler-port", default=8786, type=int, required=False,
                            help="The port to use for the dask scheduler. Defaults to 8786.")
        return parser.parse_args()

    args = parse_args()
    asyncio.run(start_api(**args.__dict__))


def launch_with_cluster():

    def parse_args() -> Namespace:
        usage = '''
            stochss-compute-cluster -p PORT
        '''
        desc = '''
            Startup script for a StochSS-Compute cluster.
            StochSS-Compute is a server and cache that anonymizes StochSS simulation data.
            Uses Dask, a Python parallel computing library.   
        '''
        parser = ArgumentParser(description=desc, add_help=True, usage=usage, conflict_handler='resolve')

        server = parser.add_argument_group('Server')
        server.add_argument("-p", "--port", default=29681, type=int, required=False,
                            help="The port to use for the server. Defaults to 29681.")
        
        cache = parser.add_argument_group('Cache')
        cache.add_argument('-c', '--cache', default='cache/', required=False, help='Path to use for the cache.')

        dask = parser.add_argument_group('Dask')
        dask.add_argument("-H", "--dask-host", default=None, required=False,
                            help="The host to use for the dask scheduler. Defaults to localhost.")
        dask.add_argument("-P", "--dask-scheduler-port", default=0, type=int, required=False,
                            help="The port to use for the dask scheduler. 0 for a random port. Defaults to a random port.")
        dask.add_argument('-W', '--dask-n-workers', default=None, type=int, required=False, help='Configure the number of workers. Defaults to one per core.')
        dask.add_argument('-T', '--dask-threads-per-worker', default=None, required=False, type=int, help='Configure the threads per worker. Default will let Dask decide based on your CPU.')
        dask.add_argument('--dask-processes', default=None, required=False, type=bool, help='Whether to use processes (True) or threads (False). Defaults to True, unless worker_class=Worker, in which case it defaults to False.')
        dask.add_argument('-D', '--dask-dashboard-address', default=':8787', required=False, help='Address on which to listen for the Bokeh diagnostics server like ‘localhost:8787’ or ‘0.0.0.0:8787’. Defaults to ‘:8787’. Set to None to disable the dashboard. Use ‘:0’ for a random port.')
        dask.add_argument('-N', '--dask-name', default=None, required=False, help='A name to use when printing out the cluster, defaults to type name.')

        return parser.parse_args()

    args = parse_args()

    dask_args = {}
    for (arg, value) in vars(args).items():
        if arg.startswith('dask_'):
            dask_args[arg[5:]] = value
    print('Launching Dask Cluster...')
    cluster = LocalCluster(**dask_args)
    tokens = cluster.scheduler_address.split(':')
    dask_host = tokens[1][2:]
    dask_port = int(tokens[2]) 
    print(f'Scheduler Address: <{cluster.scheduler_address}>')
    for i, worker in cluster.workers.items():
        print(f'Worker {i}: {worker}')
    
    print(f'Dashboard Link: <{cluster.dashboard_link}>\n')

    try:
        asyncio.run(start_api(port=args.port, cache=args.cache, dask_host=dask_host, dask_scheduler_port=dask_port))
    except KeyboardInterrupt:
        cluster.close()
