

# Tutorial-specific dependencies
# import sys
# import os            # used to set $PATH
# sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '../')))
from distributed import Client
from time import sleep

import flask
from stochss_compute.api import start_api
# from stochss_compute import RemoteSimulation, ComputeServer
# import numpy
# import gillespy2
# import subprocess         # used to run the api server in the background

# GillesPy2
# StochSS-Compute
# Dask

# api_server

if __name__ == "__main__":
    client = Client()
    print(client)
    sleep(10)
    # client
    dask_port = client.scheduler.addr.split(":")[2]
    print(dask_port)
    flask_attempt_port = 1234
    while True:
        try:
            start_api(host="0.0.0.0", port=1234, debug=True)
            break
        except OSError as e:
            if e.errno == 98:
                print(f"Port {flask_attempt_port} in use. Trying {flask_attempt_port+1}.")
                flask_attempt_port += 1
    # cmd = ["dask-scheduler", "", "--daskport", dask_port]
    # api_server = subprocess.Popen(cmd)
    # cmd = ["python3", "app.py", "--daskport", dask_port]
    # api_server = subprocess.Popen(cmd)
