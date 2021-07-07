from flask import Flask

from .v1 import v1_api
from .delegate import Delegate
from .delegate import DelegateConfig

from .delegate.dask_delegate import DaskDelegate
from .delegate.dask_delegate import DaskDelegateConfig

def start_api(
        host: str, 
        port: int, 
        debug: bool = False, 
        delegate_type: Delegate = DaskDelegate,
        delegate_config: DelegateConfig = DaskDelegateConfig(),
        **kwargs):
    
    """
    Start the REST API with the following arguments.

    :param host: The address to listen on. This may change depending on the use case.
        For example, this may need to be set to '0.0.0.0' if run in a container.
    :type host: str

    :param port: The port to listen on.
    :type port: int

    :param delegate: The type of delegate to be used to run simulation jobs. Defaults
        to the DaskDelegate.
    :type delegate: Delegate

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

    flask.register_blueprint(v1_api)

    # Start the REST API.
    flask.run(host=host, port=port, debug=debug, **kwargs)
