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

@results_endpoint.route("/plotplotly", methods=["POST"])
def plotplotly():
    # Attempt to parse incoming request data.
    try:
        plot_request = PlotPlotlyRequest.parse_raw(request.json)

    except ValidationError as e:
        return ErrorResponse(msg=f"Invalid request data: '{e}'").json(), 400

    job_id = f"{plot_request.result_id}_plotplotly"

    # If a job or results object does not exist for this ID, start it.
    if not delegate.job_exists(job_id) and not delegate.job_complete(job_id):
        # Hacky fix to ensure that the output plot is of the correct format.
        def make_plotplotly(results: "Results", *args, **kwargs) -> str:
            import plotly.io as plotlyio

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
