from flask import Flask

from stochss_compute.api.v1 import v1_api

# Initialize and configure Flask.
flask = Flask(__name__)
flask.config.update(
    JSONIFY_PRETTYPRINT_REGULAR=True
)

flask.register_blueprint(v1_api)