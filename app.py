from stochss_compute import api
from argparse import ArgumentParser, Namespace
from stochss_compute.api.cache.simple_disk_cache import SimpleDiskCache, SimpleDiskCacheConfig

from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig

def main():
    args = parse_args()
            
    cache_provider = SimpleDiskCache(SimpleDiskCacheConfig(args.cache))
    delegate_config = DaskDelegateConfig(host=args.dask_host, scheduler_port=args.dask_scheduler_port, cache_provider=cache_provider)

    api.start_api(host=args.host, port=args.port, debug=False, delegate_config=delegate_config)

def parse_args() -> Namespace:
    desc = '''
        StochSS-Compute is a server and cache that anonymizes StochSS simulation data.
    '''
    parser = ArgumentParser(description=desc, add_help=True, conflict_handler='resolve')

    server = parser.add_argument_group('Server')
    server.add_argument("-h", "--host", default='localhost', required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    server.add_argument("-p", "--port", default=29681, type=int, required=False,
                        help="The port to use for the flask server. Defaults to 29681.")

    cache = parser.add_argument_group('Cache')
    cache.add_argument('-c', '--cache', default=None, required=False, help='Path to use for the cache.')

    dask = parser.add_argument_group('Dask')
    dask.add_argument("-H", "--dask-host", default=None, required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    dask.add_argument("-P", "--dask-scheduler-port", default=0, type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786.")
    return parser.parse_args()

if __name__ == "__main__":
    main()