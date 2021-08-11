from __future__ import annotations

from requests import Response
from pydantic import BaseModel

from .api.v1.job import ErrorResponse

def unwrap_or_err(response_model: type[BaseModel], response: Response):
    if not response.ok:
        raise Exception(ErrorResponse.parse_raw(response.text).msg)

    return response_model.parse_raw(response.text)
