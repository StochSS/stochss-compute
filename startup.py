from typing import Dict
from distributed import Client, LocalCluster

from stochss_compute.api import start_api
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig
from argparse import ArgumentParser
from configparser import ConfigParser, NoSectionError

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
        config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)
        args = Dict()
        config.read(args.daskconfig)
        if len(config.sections()) == 0:
            print("Could not read dask config file. Using default values.")
            config = None
        else:
            for section in config.sections():
                try:
                    items = config.items(section)
                except NoSectionError:
                    print(f"Could not read dask config file: Key: {section}. Ignoring.")
                    continue
                for item in config.items(section):
                    print(item)
    # dask_cluster = LocalCluster()

    # client = Client()
    # print(client)
    # dask_port = client.scheduler.addr.split(":")[2]
    # print(dask_port)
    # delegate_config = DaskDelegateConfig()
    # delegate_config.dask_cluster_port = dask_port
    # while True:
    #     try:
    #         start_api(host="0.0.0.0", port=1234, debug=False, delegate_config=delegate_config)
    #         break
    #     except OSError as e:
    #         if e.errno == 98:
    #             print(f"Port {flask_attempt_port} in use. Trying {flask_attempt_port + 1}.")
    #             flask_attempt_port += 1
