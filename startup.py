
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

    print(dask_args)
    cluster = LocalCluster(**dask_args)
    delegate_config = DaskDelegateConfig(**dask_args, cluster=cluster)
    print(delegate_config.__dict__)

    try:
        start_api(host=args.host, port=args.port, debug=False, delegate_config=delegate_config)
    except KeyboardInterrupt:
        cluster.close()

def parse_args() -> Namespace:
    usage = '''
        startup.py -h HOST -p PORT
    '''
    desc = '''
        Server and cache that anonymizes StochSS simulation data. 
    '''
    parser = ArgumentParser(prog='StochSS-Compute', description=desc, add_help=True, usage=usage, conflict_handler='resolve')
    server = parser.add_argument_group('Server')
    dask = parser.add_argument_group('Dask')
    server.add_argument("-h", "--host", default='localhost', required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    server.add_argument("-p", "--port", default=29681, type=int, required=False,
                        help="The port to use for the flask server. Defaults to 29681.")
    dask.add_argument("-H", "--dask-host", default=None, required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    dask.add_argument("-P", "--dask-port", default=0, type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786, 0 to choose a random port.")
    dask.add_argument('-W', '--dask-n-workers', default=None, type=int, required=False, help='Number of workers. Defaults to one per core.')
    dask.add_argument('-T', '--dask-threads-per-worker', default=None, required=False, type=int, help='Number of workers. Defaults to one per core.')
    dask.add_argument('--dask-processes', default=None, required=False, type=bool, help='Whether to use processes (True) or threads (False). Defaults to True, unless worker_class=Worker, in which case it defaults to False.')
    dask.add_argument('-D', '--dask-dashboard-address', default=':8787', required=False, help='Address on which to listen for the Bokeh diagnostics server like ‘localhost:8787’ or ‘0.0.0.0:8787’. Defaults to ‘:8787’. Set to None to disable the dashboard. Use ‘:0’ for a random port.')
    dask.add_argument('-N', '--dask-name', default=None, required=False, help='Address on which to listen for the Bokeh diagnostics server like ‘localhost:8787’ or ‘0.0.0.0:8787’. Defaults to ‘:8787’. Set to None to disable the dashboard. Use ‘:0’ for a random port.')
    return parser.parse_args()


if __name__ == "__main__":
    main()
