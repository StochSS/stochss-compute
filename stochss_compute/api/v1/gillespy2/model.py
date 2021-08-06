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

    model_id = f"{run_request.model.get_json_hash()}-run"

    # If neither job or results already exist, start it.
    if not delegate.job_exists(model_id) and not delegate.job_complete(model_id):
        # `model` is actually a pydantic wrapper around gillespy2.Model.
        # Use the `name` attributed to access the instance of the parent.
        model = run_request.model.name

        delegate.start_job(model_id, gillespy2.core.Model.run, model, *run_request.args, **run_request.kwargs)

    # Return the status of the currently running job.
    job_status = delegate.job_status(model_id)
    return JobStatusResponse(
        job_id=model_id,
        status_id=job_status.status_id,
        status_msg=job_status.status_text,
        is_complete=job_status.is_done,
        has_failed=job_status.has_failed
    ).json(), 200
