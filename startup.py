from distributed import Client, LocalCluster

from stochss_compute.api import start_api
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig
from argparse import ArgumentParser
from configparser import ConfigParser

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=False,
                        help="The port to use for the flask server. Defaults to 1234.")
    parser.add_argument("--host", required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    # parser.add_argument("-P", "--daskport", type=int, required=False,
                        # help="The port to use for the dask scheduler. Defaults to 8786.")
    parser.add_argument("-D","--daskconfig", required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    args = parser.parse_args()
    
    flask_attempt_port = 1234
    if args.port is not None:
        flask_attempt_port = args.port
    flask_host = "localhost"
    if args.host is not None:
        flask_host = args.host
    if args.daskconfig is not None:
        config = ConfigParser()
        try:
            config.read(args.daskconfig)
    dask_cluster = LocalCluster()

    client = Client()
    print(client)
    dask_port = client.scheduler.addr.split(":")[2]
    print(dask_port)
    delegate_config = DaskDelegateConfig()
    delegate_config.dask_cluster_port = dask_port
    while True:
        try:
            start_api(host="0.0.0.0", port=1234, debug=False, delegate_config=delegate_config)
            break
        except OSError as e:
            if e.errno == 98:
                print(f"Port {flask_attempt_port} in use. Trying {flask_attempt_port + 1}.")
                flask_attempt_port += 1
