import asyncio
from tornado.web import Application
from stochss_compute.server.run import RunHandler
from stochss_compute.server.status import StatusHandler
import os
from argparse import ArgumentParser, Namespace

def make_app(args):
    scheduler_address = f'{args.dask_host}:{args.dask_scheduler_port}'
    print(f'Scheduler Address: {scheduler_address}')
    return Application([
        (r"/api/v2/simulation/gillespy2/run", RunHandler, {'scheduler_address': scheduler_address, 'cache_dir': args.cache}),
        (r"/api/v2/simulation/gillespy2/(?P<results_id>.*?)/status", StatusHandler, {'scheduler_address': scheduler_address, 'cache_dir': args.cache}),
        # (r"/api/v2/simulation/gillespy2/(?P<results_id>.*?)/cache", CacheHandler, {'scheduler_address': scheduler_address, 'cache_dir': args.cache}),
    ])

async def main():
    args = parse_args()
            
    if os.path.exists(args.cache):
        # load cache ?
        pass
    else:
        os.mkdir(args.cache)
        
    app = make_app(args)
    app.listen(args.port)
    await asyncio.Event().wait()

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
    cache.add_argument('-c', '--cache', default='cache/', required=False, help='Path to use for the cache.')

    dask = parser.add_argument_group('Dask')
    dask.add_argument("-H", "--dask-host", default='localhost', required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    dask.add_argument("-P", "--dask-scheduler-port", default=8786, type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786.")
    return parser.parse_args()

if __name__ == "__main__":
    asyncio.run(main())