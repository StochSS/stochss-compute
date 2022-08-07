import asyncio
from tornado.web import Application
from api import RunHandler
import os
from argparse import ArgumentParser, Namespace

def make_app(scheduler_address):
    return Application([
        (r"/run", RunHandler, {'scheduler_address': scheduler_address}),
        # (r"/run", RunHandler, kwargs),
    ])

async def main():
    args = parse_args()
            
    scheduler_address = f'{args.dask_host}:{args.dask_scheduler_port}'
    if os.path.exists(args.cache):
        # load cache ?
        pass
    else:
        os.mkdir(args.cache)
    app = make_app(scheduler_address)
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