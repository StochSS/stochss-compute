import json

from gillespy2.core import Model
from pydantic import BaseModel

from flask import request
from flask import Blueprint

from .apiutils import delegate

class StartJobRequest(BaseModel):
    job_id: str
    model: str
    args: str
    kwargs: str

class StartJobResponse(BaseModel):
    job_id: str
    msg: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status_id: int
    status_msg: str
    is_complete: bool
    has_failed: bool

class JobStopResponse(BaseModel):
    job_id: str
    msg: str
    success: bool

class ErrorResponse(BaseModel):
    msg: str

v1_job = Blueprint("V1 Job API Endpoint", __name__, url_prefix="/job")

@v1_job.route("/start", methods=["POST"])
def start_job():
    request_obj = StartJobRequest.parse_raw(request.json)

    if delegate.job_complete(request_obj.job_id):
        return ErrorResponse(
            msg=f"The job with id '{request_obj.job_id} has already completed."
        ).json(), 400

    if delegate.job_exists(request_obj.job_id):
        return StartJobResponse(
            job_id=request_obj.job_id,
            msg="The job has already been started.",
            status=f"/v1/job/{request_obj.job_id}/status"
        ).json(), 202

    model = Model.from_json(request_obj.model)
    kwargs = json.loads(request_obj.kwargs)

    from gillespy2.solvers import SSACSolver
    kwargs["solver"] = SSACSolver

    if not "number_of_trajectories" in kwargs:
        delegate.start_job(request_obj.job_id, Model.run, model, **kwargs)

    else:
        trajectories = kwargs["number_of_trajectories"]
        del kwargs["number_of_trajectories"]

        # Hacky, but it works for now.
        keys = [f"{request_obj.job_id}/trajectory_{i}" for i in range(0, trajectories)]
        delegate.client.scatter([model, kwargs])

        dependencies = delegate.client.map(Model.run, [model] * trajectories, **kwargs, key=keys)

        def test_job(*args, **kwargs):
            data = []

            for result in args:
                data = data + result.data

            from gillespy2.core import Results
            return Results(data)

        delegate.start_job(request_obj.job_id, test_job, *dependencies)

    return StartJobResponse(
        job_id=request_obj.job_id,
        msg="The job has been successfully started.",
        status=f"/v1/job/{request_obj.job_id}/status"
    ).json(), 202

@v1_job.route("/<string:job_id>/status")
def job_status(job_id: str):
    # Check if the job has finished.
    if not delegate.job_exists(job_id) and not delegate.job_complete(job_id):
        return ErrorResponse(
            msg=f"A job with id '{job_id}' does not exist."
        ).json(), 404

    job_status = delegate.job_status(job_id)

    return JobStatusResponse(
        job_id=job_id,
        status_id=job_status.status_id,
        status_msg=job_status.status_text,
        is_complete=job_status.is_done,
        has_failed=job_status.has_failed
    ).json(), 200

@v1_job.route("/<string:job_id>/results")
def job_results(job_id: str):
    if not delegate.job_complete(job_id):
        return ErrorResponse(
            msg=f"The job with id {job_id} is not yet complete."
        ).json(), 400

    job_results = delegate.job_results(job_id)
    return job_results.to_json(), 200

@v1_job.route("/<string:job_id>/stop", methods=["POST"])
def job_stop(job_id: str):
    if not delegate.job_exists(job_id):
        return ErrorResponse(
            msg=f"A job with id {job_id} does not exist."
        ).json(), 404

    if not delegate.stop_job(job_id):
        return JobStopResponse(
            job_id=job_id,
            msg=f"Failed to stop job with id '{job_id}'.",
            success=False
        ).json(), 500

    return JobStopResponse(
        job_id=job_id,
        msg=f"Job with id '{job_id}' has been stopped.",
        success=True
    ).json(), 200

