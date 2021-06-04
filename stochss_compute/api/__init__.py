from os import name

from stochss_compute.api.v1 import v1_api_blueprint
from stochss_compute.api.delegate.dask_delegate import DaskDelegate
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig

# Initialize and configure the compute delegate.
delegate_config = DaskDelegateConfig()
delegate = DaskDelegate(delegate_config)

# Validate the connection.
if False in (delegate.connect(), delegate.test_connection()):
    raise Exception("Delegate connection failed.")

# Initialize and configure Flask.
flask = Flask(__name__)
flask.config.update(
    JSONIFY_PRETTYPRINT_REGULAR=True
)

flask.register_blueprint(v1_api_blueprint)