import bz2
import dill

import plotly.io as plotlyio

from flask import Blueprint
from flask import make_response
from gillespy2.core import Results

from .apiutils import delegate
from .job import ErrorResponse

v1_result = Blueprint("V1 Result API Endpoint", __name__, url_prefix="result/")

@v1_result.route("/<string:result_id>/get", methods=["GET"])
def get_results(result_id: str):
    if not delegate.job_complete(result_id):
        return ErrorResponse(msg="A result with this ID does not yet exist."), 404

    results_json = delegate.job_results(result_id).to_json()
    compressed_results = bz2.compress(results_json.encode())

    response = make_response(compressed_results)
    response.headers["Content-Encoding"] = "bzip2"

    return response, 200


@v1_result.route("/<string:result_id>/exists", methods=["GET"])
def results_exist(result_id: str):
    if not delegate.job_complete(result_id):
        return "False", 404

    return "True", 200

@v1_result.route("/<string:result_id>/plotplotly", methods=["GET"])
def make_plot(result_id: str):
    # Ensure that a result with this ID exists.
    if not delegate.job_complete(result_id):
        return "Something broke", 404

    # Grab the results.
    results: Results = delegate.job_results(result_id)

    # Plot the figure without rendering, returning the backing datastructure.
    results_plot = results.plotplotly(return_plotly_figure=True)

    # Generate plot JSON, encode, and compress.
    plot_json = plotlyio.to_json(results_plot)
    compressed_plot = bz2.compress(plot_json.encode())

    # Create and return the HTTP response.
    response = make_response(compressed_plot)
    response.headers["Content-Encoding"] = "bzip2"

    return response, 200
