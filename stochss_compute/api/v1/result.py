import os
import bz2
import tempfile

import plotly.io as plotlyio

from flask import Blueprint
from flask import make_response

from matplotlib import pyplot

from gillespy2.core import Results

from .apiutils import delegate

from .job import ErrorResponse
from .job import StartJobResponse

v1_result = Blueprint("V1 Result API Endpoint", __name__, url_prefix="result/")

@v1_result.route("/<string:result_id>/get", methods=["GET"])
def get_results(result_id: str):
    if not delegate.job_complete(result_id):
        return ErrorResponse(msg="A result with this ID does not yet exist.").json(), 404

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

@v1_result.route("/<string:result_id>/average_ensemble", methods=["POST"])
def make_average_ensemble(result_id: str):
    # Make sure we can grab a result with this ID.
    job_id = f"average_ensemble-{result_id}"

    if delegate.job_exists(job_id):
        return StartJobResponse(
            job_id=job_id,
            msg="The job has already been started.",
            status=f"/v1/job/{job_id}/status"
        ).json(), 202

    from gillespy2.core import Results
    delegate.start_job(job_id, Results.average_ensemble, f"result://{result_id}")

    return StartJobResponse(
        job_id=job_id,
        msg="The job has been successfully started.",
        status=f"/v1/job/{job_id}/status"
    ).json(), 202

@v1_result.route("/<string:result_id>/plot", methods=["GET"])
def make_plot(result_id: str):
    # Make sure we can grab a result with this ID.
    if not delegate.job_complete(result_id):
        return "Something broke", 404

    # Grab the results.
    results: Results = delegate.job_results(result_id)

    # Swap the pyplot backend so the Results#plot call wont try to write to a GUI.
    pyplot.switch_backend("template")

    # Write the plot as a .png to the tempfile.
    _, temp = tempfile.mkstemp(suffix=".png")
    results.plot(save_png=temp)

    # Read the contents of the temp file and cleanup.
    with open(temp, "rb") as infile:
        plot_bytes = infile.read()

    os.remove(temp)

    compressed_plot = bz2.compress(plot_bytes)

    response = make_response(compressed_plot)
    response.headers["Content-Encoding"] = "bzip2"

    return response, 200

@v1_result.route("/<string:result_id>/plotplotly", methods=["GET"])
def make_plotplotly(result_id: str):
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
