
from stochss_compute.api import start_api
from stochss_compute.api.cache.simple_disk_cache import SimpleDiskCache, SimpleDiskCacheConfig
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig
from argparse import ArgumentParser, Namespace
from distributed import LocalCluster

def main():
    args = parse_args()

    dask_args = {}
    for (arg, value) in vars(args).items():
        if arg.startswith('dask_'):
            dask_args[arg[5:]] = value

    cluster = LocalCluster(**dask_args)
    tokens = cluster.scheduler_address.split(':')
    dask_host = tokens[1][2:]
    dask_port = int(tokens[2]) 
    print(f'Scheduler Address: <{cluster.scheduler_address}>')
    for i, worker in cluster.workers.items():
        print(f'Worker {i}: {worker}')
    
    print(f'Dashboard Link: <{cluster.dashboard_link}>')

    cache_provider = SimpleDiskCache(SimpleDiskCacheConfig(root_dir=args.cache))
    delegate_config = DaskDelegateConfig(host=dask_host, scheduler_port=dask_port, cache_provider=cache_provider)

    try:
        start_api(host=args.host, port=args.port, debug=False, delegate_config=delegate_config)
    except KeyboardInterrupt:
        cluster.close()

def parse_args() -> Namespace:
    usage = '''
        startup.py -h HOST -p PORT
    '''
    desc = '''
        Startup script for a StochSS-Compute cluster.
        StochSS-Compute is a server and cache that anonymizes StochSS simulation data.
        Uses Dask, a Python parallel computing library.   
    '''
    parser = ArgumentParser(description=desc, add_help=True, usage=usage, conflict_handler='resolve')

    server = parser.add_argument_group('Server')
    server.add_argument("-h", "--host", default='localhost', required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    server.add_argument("-p", "--port", default=29681, type=int, required=False,
                        help="The port to use for the flask server. Defaults to 29681.")
    
    cache = parser.add_argument_group('Cache')
    cache.add_argument('-c', '--cache', default='sd-cache/', required=False, help='Path to use for the cache.')

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


if __name__ == "__main__":
    main()
