from typing import Any
from typing import List
from typing import Dict

import gillespy2;
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    msg: str

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

class BaseModel(BaseModel):
    pass

class Model(gillespy2.Model):
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
    args: List = []
    kwargs: Dict = {}

    class Config:
        json_encoders = {gillespy2.core.Model: lambda model: Model.__serialize__(model)}

class PlotPlotlyRequest(BaseModel):
    result_id: str
    args: List[str] = []
    kwargs: Dict[str, Any] = {}

class AverageEnsembleRequest(BaseModel):
    result_id: str
