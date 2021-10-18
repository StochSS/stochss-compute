from pydantic import BaseModel

class ErrorResponse(BaseModel):
    msg: str
