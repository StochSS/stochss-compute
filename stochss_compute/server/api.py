'''
stochss_compute.server.api
'''
# StochSS-Compute is a tool for running and caching GillesPy2 simulations remotely.
# Copyright (C) 2019-2023 GillesPy2 and StochSS developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import asyncio
import subprocess
from tornado.web import Application
from stochss_compute.server.is_cached import IsCachedHandler
from stochss_compute.server.run import RunHandler
from stochss_compute.server.sourceip import SourceIpHandler
from stochss_compute.server.status import StatusHandler
from stochss_compute.server.results import ResultsHandler

def _make_app(dask_host, dask_scheduler_port, cache):
    scheduler_address = f'{dask_host}:{dask_scheduler_port}'
    return Application([
        (r"/api/v2/simulation/gillespy2/run", RunHandler,
            {'scheduler_address': scheduler_address, 'cache_dir': cache}),
        (r"/api/v2/simulation/gillespy2/(?P<results_id>.*?)/(?P<n_traj>[1-9]\d*?)/(?P<task_id>.*?)/status",
            StatusHandler, {'scheduler_address': scheduler_address, 'cache_dir': cache}),
        (r"/api/v2/simulation/gillespy2/(?P<results_id>.*?)/(?P<n_traj>[1-9]\d*?)/results",
            ResultsHandler, {'cache_dir': cache}),
        (r"/api/v2/cache/gillespy2/(?P<results_id>.*?)/(?P<n_traj>[1-9]\d*?)/is_cached",
            IsCachedHandler, {'cache_dir': cache}),
        (r"/api/v2/cloud/sourceip", SourceIpHandler),
    ])

async def start_api(
        port = 29681,
        cache = 'cache/',
        dask_host = 'localhost',
        dask_scheduler_port = 8786,
        rm = False,
        ):
    """
    Start the REST API with the following arguments.

    :param port: The port to listen on.
    :type port: int

    :param cache: The cache directory path.
    :type cache: str

    :param dask_host: The address of the dask cluster.
    :type dask_host: str

    :param dask_scheduler_port: The port of the dask cluster.
    :type dask_scheduler_port: int

    :param rm: Delete the cache when exiting this program.
    :type rm: bool
    """
    # clean up lock files here
    cache_path = os.path.abspath(cache)
    app = _make_app(dask_host, dask_scheduler_port, cache)
    app.listen(port)
    print(f'StochSS-Compute listening on: :{port}')
    print(f'Cache directory: {cache_path}')
    print(f'Connecting to Dask scheduler at: {dask_host}:{dask_scheduler_port}\n')

    try:
        await asyncio.Event().wait()
    except asyncio.exceptions.CancelledError as error:
        print(error)
    finally:
        if rm and os.path.exists(cache_path):
            print('Removing cache...', end='')
            subprocess.Popen(['rm', '-r', cache_path])
            print('OK')
            