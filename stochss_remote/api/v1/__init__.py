from flask import Blueprint
from flask_restx import Api

from .job import api as job_api

blueprint = Blueprint("api", __name__, url_prefix="/v1")
api = Api(blueprint, title="V1 API Endpoints", version="0.1")

api.add_namespace(job_api)