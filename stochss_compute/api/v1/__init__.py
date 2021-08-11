from flask import Blueprint

from .job import v1_job
from .result import v1_result

v1_api = Blueprint("stochss-compute API V1", __name__, url_prefix="/api/v1")

v1_api.register_blueprint(v1_job)
v1_api.register_blueprint(v1_result)

print("V1 API has been initialized.")
