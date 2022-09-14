from tornado.web import RequestHandler



# class SourceIpRequest(BaseModel):
#     cloud_key: str

# class SourceIpResponse(BaseModel):
#     source_ip: str

# class ErrorResponse(BaseModel):
#     msg: str


# v1_cloud = Blueprint("Cloud API endpoint", __name__, url_prefix='/cloud')

# @v1_cloud.route('/sourceip', methods=['POST'])
# def source_ip():
#     try:
#         source_ip_request = SourceIpRequest.parse_raw(request.json)
#     except ValidationError as e:
#         return ErrorResponse(msg=f"Invalid request data: '{e}'").json(), 400

#     if source_ip_request.cloud_key == os.environ.get('CLOUD_LOCK'):
#         return SourceIpResponse(source_ip=request.remote_addr).json(), 200
#     else:
#         return ErrorResponse(msg='Access denied.').json(), 400