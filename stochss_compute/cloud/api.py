import json
from pydantic import BaseModel

from flask import request
from flask import Blueprint

class LockRequest(BaseModel):
    cloud_key: str

class LockResponse(BaseModel):
    source_ip: str

v1_cloud = Blueprint("Cluster API endpoint", __name__, url_prefix='/lock')

@v1_cloud.route('/lock', methods=['POST'])
def source_ip():
    pass