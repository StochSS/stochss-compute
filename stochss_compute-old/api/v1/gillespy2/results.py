from typing import Any
from typing import List
from typing import Dict

from ..apiutils import delegate
from ..job import JobStatusResponse
from ..dataclass import ErrorResponse

from gillespy2.core import Results

from flask import request
from flask import Blueprint

from pydantic import BaseModel
from pydantic import ValidationError

results_endpoint = Blueprint("V1 GillesPy2 Results API Endpoint", __name__, url_prefix="/results")

class PlotPlotlyRequest(BaseModel):
    result_id: str
    args: List[str] = []
    kwargs: Dict[str, Any] = {}

class AverageEnsembleRequest(BaseModel):
    result_id: str

@results_endpoint.route("/plotplotly", methods=["POST"])
def plotplotly():
    # Attempt to parse incoming request data.
    try:
        plot_request = PlotPlotlyRequest.parse_raw(request.json)

    except ValidationError as e:
        return ErrorResponse(msg=f"Invalid request data: '{e}'").json(), 400

    job_id = f"{plot_request.result_id}-plotplotly"

    # Ensure that the parent job (result_id) exists or has saved results.
    if not delegate.job_exists(plot_request.result_id) and not delegate.job_complete(plot_request.result_id):
        return ErrorResponse(msg=f"No parent job with ID '{plot_request.result_id}' exists.").json(), 400

    # If a job or results object does not exist for this ID, start it.
    if not delegate.job_exists(job_id) and not delegate.job_complete(job_id):
        # Hacky fix to ensure that the output plot is of the correct format.
        def make_plotplotly(results_json: str, *args, **kwargs) -> str:
            import plotly.io as plotlyio

            results = Results.from_json(results_json)
            plot = Results.plotplotly(results, return_plotly_figure=True, **kwargs)
            plot_json = plotlyio.to_json(plot)

            return plot_json
                
        delegate.start_job(job_id, make_plotplotly, f"result://{plot_request.result_id}", *plot_request.args, **plot_request.kwargs)

    # Return the status of the currently running job.
    job_status = delegate.job_status(job_id)
    return JobStatusResponse(
        job_id=job_id,
        status_id=job_status.status_id,
        status_msg=job_status.status_text,
        is_complete=job_status.is_done,
        has_failed=job_status.has_failed
    ).json(), 200

@results_endpoint.route("/average_ensemble", methods=["POST"])
def make_average_ensemble():
    # Attempt to parse incoming request data.
    try:
        ensemble_request = AverageEnsembleRequest.parse_raw(request.json)

    except ValidationError as e:
        return ErrorResponse(msg=f"Invalid request data: '{e}'").json(), 400

    # Make sure we can grab a result with this ID.
    result_id = ensemble_request.result_id
    job_id = f"{result_id}-average_ensemble"

    # Ensure that the parent job (result_id) exists or has saved results.
    if not delegate.job_exists(result_id) and not delegate.job_complete(result_id):
        return ErrorResponse(msg=f"No parent job with ID '{result_id}' exists.").json(), 400

    # If a job or results object does not exist for this ID, start it.
    if not delegate.job_exists(job_id) and not delegate.job_complete(job_id):
        def results_to_json(results_json):
            results = Results.from_json(results_json)
            return results.average_ensemble().to_json()

        delegate.start_job(job_id, results_to_json, f"result://{result_id}")

    # Return the status of the currently running job.
    job_status = delegate.job_status(job_id)
    return JobStatusResponse(
        job_id=job_id,
        status_id=job_status.status_id,
        status_msg=job_status.status_text,
        is_complete=job_status.is_done,
        has_failed=job_status.has_failed
    ).json(), 200
