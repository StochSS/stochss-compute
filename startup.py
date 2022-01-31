

# Tutorial-specific dependencies
import sys
import os            # used to set $PATH
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '../')))
from distributed import Client
from stochss_compute import RemoteSimulation, ComputeServer
import numpy
import gillespy2
import subprocess         # used to run the api server in the background

# GillesPy2
# StochSS-Compute
# Dask

# api_server

if __name__ == "__main__":
    client = Client()
    # client
    dask_port = client.scheduler.addr.split(":")[2]
    # dask_port

    cmd = ["python3", "app.py", "--daskport", dask_port]
    api_server = subprocess.Popen(cmd)
