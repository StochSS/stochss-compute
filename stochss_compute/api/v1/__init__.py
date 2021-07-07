from flask import Blueprint
from stochss_compute.api.v1.job import v1_job

v1_api = Blueprint("stochss-compute API V1", __name__, url_prefix="/api/v1")
v1_api.register_blueprint(v1_job)

print("V1 API has been initialized.")
