import multiprocessing as mp
import os
import unittest
from stochss_compute import start_api
from distributed import Client
import time
import coverage
import asyncio
import stochss_compute

def _sssc():
    # cov = coverage.Coverage(source_pkgs=('stochss_compute',), config_file='.covrc')
    # cov.start()
    kwargs = {
        'dask_scheduler_port': 8786
    }
    asyncio.run(start_api(**kwargs))
    # cov.stop()
    # cov.save()
    # print(cov.html_report())

if __name__ == '__main__':
    client = Client()
    dask_scheduler_port = client.scheduler.addr.split(":")[2]
    kwargs = {
        'dask_scheduler_port': dask_scheduler_port
    }

    
    sssc = mp.Process(target=_sssc)
    sssc.start()
    time.sleep(5)
    sssc.terminate()
    client.close()