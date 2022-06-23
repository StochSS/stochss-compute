from stochss_compute import api
from argparse import ArgumentParser, Namespace

from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig

def main():
    args = parse_args()
    dask_args = {}
    for (arg, value) in vars(args).items():
        if arg.startswith('dask_'):
            dask_args[arg[5:]] = value
            
    delegate_config = DaskDelegateConfig(**dask_args)

    api.start_api(host=args.host, port=args.port, debug=False, delegate_config=delegate_config)

def parse_args() -> Namespace:
    desc = '''
        StochSS-Compute is a server and cache that anonymizes StochSS simulation data.
    '''
    parser = ArgumentParser(description=desc, add_help=True, conflict_handler='resolve')
    server = parser.add_argument_group('Server')
    dask = parser.add_argument_group('Dask')
    server.add_argument("-h", "--host", default='localhost', required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    server.add_argument("-p", "--port", default=29681, type=int, required=False,
                        help="The port to use for the flask server. Defaults to 29681.")
    dask.add_argument("-H", "--dask-host", default=None, required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    dask.add_argument("-P", "--dask-scheduler-port", default=0, type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786.")
    return parser.parse_args()

if __name__ == "__main__":
    main()