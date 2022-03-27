from __future__ import annotations

from requests import Response
from pydantic import BaseModel

from stochss_compute.api.dataclass import ErrorResponse

def unwrap_or_err(response_model: type[BaseModel], response: Response):
    if not response.ok:
        raise Exception(ErrorResponse.parse_raw(response.text).msg)

    return response_model.parse_raw(response.text)
