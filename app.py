from stochss_compute import api
import argparse

from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig

def server_start(host, port, debug=True, delegate_config=None):
    if host is None:
        host = "localhost"
    if port is None:
        port = 1234
    api.start_api(host=host, port=port, debug=debug, delegate_config=delegate_config)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=False, help="The port to use for the flask server. Defaults to 1234.")
    parser.add_argument("--host", required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    parser.add_argument("-P", "--daskport", type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786.")
    parser.add_argument("--daskhost", required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    args = parser.parse_args()

    delegate_config = DaskDelegateConfig()

    if args.daskport is not None:
        delegate_config.dask_cluster_port = args.daskport
    
    if args.daskhost is not None:
        delegate_config.dask_cluster_address = args.daskhost

    server_start(args.host, args.port, delegate_config=delegate_config)
