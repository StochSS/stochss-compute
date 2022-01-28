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

v1_memory = Blueprint("V1 Result API Endpoint", __name__, url_prefix="memory/")

@v1_memory.route("/<string:memory_id>/get", methods=["GET"])
def get_memory(memory_id: str):
    if not delegate.job_complete(memory_id):
        return ErrorResponse(msg="A memory with this ID does not yet exist.").json(), 404

    memory_json = delegate.job_results(memory_id)
    compressed_memory = bz2.compress(memory_json.encode())

    response = make_response(compressed_memory)
    response.headers["Content-Encoding"] = "bzip2"

    return response, 200


@v1_memory.route("/<string:memory_id>/exists", methods=["GET"])
def memory_exist(memory_id: str):
    if not delegate.job_complete(memory_id):
        return "False", 404

    return "True", 200

@v1_memory.route("/<string:memory_id>/average_ensemble", methods=["POST"])
def make_average_ensemble(memory_id: str):
    # Make sure we can grab a memory with this ID.
    job_id = f"average_ensemble-{memory_id}"

    if delegate.job_exists(job_id):
        return StartJobResponse(
            job_id=job_id,
            msg="The job has already been started.",
            status=f"/v1/job/{job_id}/status"
        ).json(), 202

    delegate.start_job(job_id, Results.average_ensemble, f"memory://{memory_id}")

    return StartJobResponse(
        job_id=job_id,
        msg="The job has been successfully started.",
        status=f"/v1/job/{job_id}/status"
    ).json(), 202

@v1_memory.route("/<string:memory_id>/plot", methods=["GET"])
def make_plot(memory_id: str):
    # Make sure we can grab a memory with this ID.
    if not delegate.job_complete(memory_id):
        status = delegate.job_status(memory_id)
        return status.status_text, 404

    # Grab the memory.
    memory: Results = Results.from_json(delegate.job_results(memory_id))

    # Swap the pyplot backend so the Results#plot call wont try to write to a GUI.
    pyplot.switch_backend("template")

    # Write the plot as a .png to the tempfile.
    _, temp = tempfile.mkstemp(suffix=".png")
    memory.plot(save_png=temp)

    # Read the contents of the temp file and cleanup.
    with open(temp, "rb") as infile:
        plot_bytes = infile.read()

    os.remove(temp)

    compressed_plot = bz2.compress(plot_bytes)

    response = make_response(compressed_plot)
    response.headers["Content-Encoding"] = "bzip2"

    return response, 200

@v1_memory.route("/<string:memory_id>/plotplotly", methods=["GET"])
def make_plotplotly(memory_id: str):
    # Ensure that a memory with this ID exists.
    if not delegate.job_complete(memory_id):
        return "Something broke", 404

    # Grab the memorys.
    memory: Results = delegate.job_results(memory_id)

    # Plot the figure without rendering, returning the backing datastructure.
    memorys_plot = memory.plotplotly(return_plotly_figure=True)

    # Generate plot JSON, encode, and compress.
    plot_json = plotlyio.to_json(memorys_plot)
    compressed_plot = bz2.compress(plot_json.encode())

    # Create and return the HTTP response.
    response = make_response(compressed_plot)
    response.headers["Content-Encoding"] = "bzip2"

    return response, 200
