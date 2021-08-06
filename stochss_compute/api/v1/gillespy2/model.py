from typing import List
from typing import Dict

from ..apiutils import delegate
from ..job import JobStatusResponse
from ..dataclass import ErrorResponse

import gillespy2.core

from flask import request
from flask import Blueprint

from pydantic import BaseModel
from pydantic import ValidationError

model_endpoint = Blueprint("V1 GillesPy2 Model API Endpoint", __name__, url_prefix="/model")

class Model(gillespy2.core.Model):
    @classmethod
    def __serialize__(cls, value: "Model") -> str:
        return value.to_json()

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value) -> "Model":
        if isinstance(value, str):
            return cls(Model.from_json(value))

        return value

class ModelRunRequest(BaseModel):
    model: Model
    args: List[str] = []
    kwargs: Dict[str, str] = {}

    class Config:
        json_encoders = {gillespy2.core.Model: lambda model: Model.__serialize__(model)}

@model_endpoint.route("/run", methods=["POST"])
def run():
    # Attempt to parse request data.
    try:
        run_request = ModelRunRequest.parse_raw(request.json)

    except ValidationError as e:
        return ErrorResponse(msg=f"Invalid request data: '{e}'").json(), 400

    model = run_request.model.name
    model_id = f"{model.get_json_hash()}"
    number_trajectories = int(run_request.kwargs.pop("number_of_trajectories", 1))

    # Build a list of job key values which will need to be run.
    keys = [f"{model_id}/trajectory_{i}" for i in range(number_trajectories)]

    # Run each trajectory and save in a dataset.
    dependencies = delegate.client.map(gillespy2.core.Model.run, [model] * number_trajectories, **run_request.kwargs, key=keys)
    delegate.client.publish_dataset(dependencies, name=f"{model_id}/{number_trajectories}_trajectories", override=True)

    def join_results(results):
        data = []

        for result in results:
            data = data + result.data

        from gillespy2.core import Results
        return Results(data)

    delegate.start_job(f"{model_id}/run:{number_trajectories}", join_results, dependencies)

    # Return the status of the currently running job.
    job_status = delegate.job_status(model_id)
    return JobStatusResponse(
        job_id=f"{model_id}/run:{number_trajectories}",
        status_id=job_status.status_id,
        status_msg=job_status.status_text,
        is_complete=job_status.is_done,
        has_failed=job_status.has_failed
    ).json(), 200

