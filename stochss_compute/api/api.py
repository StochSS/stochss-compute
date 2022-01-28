from __future__ import annotations

from flask import Flask

from .v1 import v1_api
from .delegate import Delegate
from .delegate import DelegateConfig

from .delegate.dask_delegate import DaskDelegate
from .delegate.dask_delegate import DaskDelegateConfig

from .cache import CacheProvider
from .cache import CacheProviderConfig
from .cache import SimpleDiskCache
from .cache import SimpleDiskCacheConfig

from dask_kubernetes import KubeCluster
import os

def start_api(
        host: str, 
        port: int, 
        debug: bool = False, 
        delegate_type: type[Delegate] = DaskDelegate,
        delegate_config: DelegateConfig = DaskDelegateConfig(),
        # kube: bool = False,
        **kwargs):
    
    """
    Start the REST API with the following arguments.

    :param host: The address to listen on. This may change depending on the use case.
        For example, this may need to be set to '0.0.0.0' if run in a container.
    :type host: str

    :param port: The port to listen on.
    :type port: int

    :param delegate_type: The type of delegate to be used to run simulation jobs. Defaults
        to DaskDelegate.
    :type delegate_type: type[Delegate]

    :param delegate_config: Delegate-specific configuration options. These will be
        passed directly to the Delegate instance. If None then the default config
        will be used.
    :type delegate_config: DelegateConfig

    :param kwargs: Additional arguments to be passed to Flask#run().
    :type kwargs: dict
    """

    # Instantiate the Flask instance on the API and register any required blueprints
    flask = Flask("stochss-compute REST API")
    flask.config.update(
        JSONIFY_PRETTYPRINT_REGULAR=True,
        DELEGATE_TYPE=delegate_type,
        DELEGATE_CONFIG=delegate_config,
    )

    # # Will return None if not being run using the kubernetes manifest where this environment variable is initialized
    # kube_dask_worker_spec = os.environ.get("WORKER_SPEC_PATH")

    # if kube_dask_worker_spec is not None:
    #     kube_cluster = KubeCluster(pod_template=kube_dask_worker_spec, n_workers=1)
    #     if debug:
    #         print("Dask KubeCluster created:")
    #         print(kube_cluster)
    #     flask.config.update(
    #         KUBE_CLUSTER=kube_cluster
    #     )

    flask.register_blueprint(v1_api)

    # use_reloader=False (prevents two KubeClusters from being created)
    # Start the REST API.
    flask.run(host=host, port=port, debug=debug, use_reloader=False, **kwargs)
