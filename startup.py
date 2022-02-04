from distributed import Client

from stochss_compute.api import start_api
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig


if __name__ == "__main__":
    client = Client()
    print(client)
    dask_port = client.scheduler.addr.split(":")[2]
    print(dask_port)
    delegate_config = DaskDelegateConfig()
    delegate_config.dask_cluster_port = dask_port
    flask_attempt_port = 1234
    while True:
        try:
            start_api(host="0.0.0.0", port=1234, debug=False, delegate_config=delegate_config)
            break
        except OSError as e:
            if e.errno == 98:
                print(f"Port {flask_attempt_port} in use. Trying {flask_attempt_port + 1}.")
                flask_attempt_port += 1
