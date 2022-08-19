from flask import Blueprint

from .model import model_endpoint
from .results import results_endpoint

v1_gillespy2 = Blueprint("V1 GillesPy2 API Endpoints", __name__, url_prefix="/gillespy2")
v1_gillespy2.register_blueprint(model_endpoint)
v1_gillespy2.register_blueprint(results_endpoint)
