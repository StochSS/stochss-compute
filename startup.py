
from stochss_compute.api import start_api
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
    print(f'Dashboard Link: <{cluster.dashboard_link}>')
    delegate_config = DaskDelegateConfig(**dask_args, cluster=cluster)

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
    parser = ArgumentParser(prog='StochSS-Compute', description=desc, add_help=True, usage=usage, conflict_handler='resolve')
    server = parser.add_argument_group('Server')
    dask = parser.add_argument_group('Dask')
    server.add_argument("-h", "--host", default='localhost', required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    server.add_argument("-p", "--port", default=29681, type=int, required=False,
                        help="The port to use for the flask server. Defaults to 29681.")
    dask.add_argument("-H", "--dask-host", default=None, required=False,
                        help="The host to use for the dask scheduler. Only use if you will be connecting to your own dask cluster. Defaults to localhost.")
    dask.add_argument("-P", "--dask-port", default=0, type=int, required=False,
                        help="The port to use for the dask scheduler. Only use if you will be connecting to your own dask cluster. Defaults to 8786.")
    dask.add_argument('-W', '--dask-n-workers', default=None, type=int, required=False, help='Configure the number of workers. Defaults to one per core.')
    dask.add_argument('-T', '--dask-threads-per-worker', default=None, required=False, type=int, help='Configure the threads per worker. Default will let Dask decide.')
    dask.add_argument('--dask-processes', default=None, required=False, type=bool, help='Whether to use processes (True) or threads (False). Defaults to True, unless worker_class=Worker, in which case it defaults to False.')
    dask.add_argument('-D', '--dask-dashboard-address', default=':8787', required=False, help='Address on which to listen for the Bokeh diagnostics server like ‘localhost:8787’ or ‘0.0.0.0:8787’. Defaults to ‘:8787’. Set to None to disable the dashboard. Use ‘:0’ for a random port.')
    dask.add_argument('-N', '--dask-name', default=None, required=False, help='Address on which to listen for the Bokeh diagnostics server like ‘localhost:8787’ or ‘0.0.0.0:8787’. Defaults to ‘:8787’. Set to None to disable the dashboard. Use ‘:0’ for a random port.')
    return parser.parse_args()


if __name__ == "__main__":
    main()
