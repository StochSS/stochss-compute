from flask import Blueprint

from .job import v1_job
from .memory import v1_memory
from .gillespy2 import v1_gillespy2

v1_api = Blueprint("stochss-compute API V1", __name__, url_prefix="/api/v1")

v1_api.register_blueprint(v1_job)
v1_api.register_blueprint(v1_memory)
v1_api.register_blueprint(v1_gillespy2)

# print("V1 API has been initialized.")
