from flask import Blueprint

from .job import v1_job
from .result import v1_result
from .gillespy2 import v1_gillespy2

v1_api = Blueprint("stochss-compute API V1", __name__, url_prefix="/api/v1")

v1_api.register_blueprint(v1_job)
v1_api.register_blueprint(v1_result)
v1_api.register_blueprint(v1_gillespy2)

print("V1 API has been initialized.")
