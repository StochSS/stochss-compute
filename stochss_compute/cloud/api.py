import os
from pydantic import BaseModel, ValidationError

from flask import request
from flask import Blueprint

class LockRequest(BaseModel):
    cloud_key: str

class LockResponse(BaseModel):
    source_ip: str

class ErrorResponse(BaseModel):
    msg: str


v1_cloud = Blueprint("Cloud API endpoint", __name__, url_prefix='/cloud')

@v1_cloud.route('/lock', methods=['POST'])
def source_ip():
    try:
        lock_request = LockRequest.parse_raw(request.json)
    except ValidationError as e:
        return ErrorResponse(msg=f"Invalid request data: '{e}'").json(), 400

    print(f'>>>>>>>>>>{lock_request.cloud_key}')
    cloud_lock = os.environ.get('CLOUD_LOCK')
    print(f'>>>>>>>>>>{cloud_lock}')
    if lock_request.cloud_key == os.environ.get('CLOUD_LOCK'):
        return LockResponse(source_ip=request.remote_addr).json(), 200
    else:
        return ErrorResponse(msg='Access denied.').json(), 400