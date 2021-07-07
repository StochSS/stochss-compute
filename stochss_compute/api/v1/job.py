from gillespy2 import Model
from pydantic import BaseModel

from flask import g
from flask import request
from flask import Blueprint
from flask import current_app
from flask import make_response

from werkzeug.local import LocalProxy

from stochss_compute.api.delegate.dask_delegate import DaskDelegate
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig

class StartJobRequest(BaseModel):
    job_id: str
    model: str

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

def get_delegate():
    if "delegate" in g:
        return g.delegate

    delegate_config = current_app.config["DELEGATE_CONFIG"]
    delegate_type = current_app.config["DELEGATE_TYPE"]

    delegate = delegate_type(delegate_config)

    if False in (delegate.connect(), delegate.test_connection()):
        raise Exception("Delegate connection failed.")

    return delegate

delegate = LocalProxy(get_delegate)

@v1_job.route("/start", methods=["POST"])
def start_job():
    request_obj = StartJobRequest.parse_raw(request.json)

    if delegate.job_exists(request_obj.job_id):
        return ErrorResponse(
            msg=f"A job with id '{request_obj.job_id}' already exists."
        ).json(), 400

    model = Model.from_json(request_obj.model)
    delegate.start_job(request_obj.job_id, model.run)

    return StartJobResponse(
        job_id=request_obj.job_id,
        msg="The job has been successfully started.",
        status=f"/v1/job/{request_obj.job_id}/status"
    ).json(), 202

@v1_job.route("/<string:job_id>/status")
def job_status(job_id: str):
    job_status = delegate.job_status(job_id)

    return make_response(JobStatusResponse(
        job_id=job_id,
        status_id=job_status.status_id,
        status_msg=job_status.status_text,
        is_complete=job_status.is_done,
        has_failed=job_status.has_failed
    ).dict(), 200)

@v1_job.route("/<string:job_id>/results")
def job_results(job_id: str):
    if not delegate.job_exists(job_id) and not delegate.job_complete(job_id):
        return ErrorResponse(
            msg=f"A job with id '{job_id}' does not exist."
        ).dict(), 404

    if not delegate.job_status(job_id).is_done:
        return ErrorResponse(
            msg=f"The job with id {job_id} is not yet complete."
        ).dict(), 400

    job_results = delegate.job_results(job_id)
    return job_results.to_json(), 200

@v1_job.route("/<string:job_id>/stop")
def job_stop(job_id: str):
    if not delegate.job_exists(job_id):
        return ErrorResponse(
            msg=f"A job with id {job_id} does not exist."
        ).dict(), 404

    if not delegate.stop_job(job_id):
        return JobStopResponse(
            job_id=job_id,
            msg=f"Failed to stop job with id '{job_id}'.",
            success=False
        ).dict(), 500

    return JobStopResponse(
        job_id=job_id,
        msg=f"Job with id '{job_id}' has been stopped.",
        success=True
    ).dict(), 200

# class Create(MethodView):
#     parser = reqparse.RequestParser()
#     parser.add_argument("sim", type=str, required=True, help="The name of the simulation to be associated with this job.")
#     parser.add_argument("hash", type=str, required=True, help="The hash of the model to be run.")
# 
#     def post(self):
#         args = self.parser.parse_args()
#         id = Simulation(args["type"], args["hash"], args["model"], args["param"]).run()
# 
# class Start(MethodView):
#     parser = reqparse.RequestParser()
# 
#     parser.add_argument("type", type=str, required=True, help="The type of simulation to be associated with this job.")
#     parser.add_argument("hash", type=str, required=True, help="The hash of the model to be run.")
#     parser.add_argument("model", type=str, required=True, help="The model to be run.")
#     parser.add_argument("params", type=str, required=False, help="Model run parameters.")
#     
#     def post(self):
#         args = self.parser.parse_args()
# 
#         delegate.start_job()
#         id = Simulation(args["type"], args["hash"], args["model"], args["params"]).run()
# 
#         return { "status": f"/v1/job/status/{id}" }
# 
# class Status(MethodView):
#     parser = reqparse.RequestParser()
#     parser.add_argument("id", type=str, required=True, help="The ID of the job.")
# 
#     def get(self, id):
#         status = Simulation.status(id)
# 
#         if status.status_id == JobState.SUCCESS:
#             return {
#                 "status_id": status.status_id,
#                 "status_text": status.status_text,
#                 "results": Simulation.result(id)
#             }
# 
#         return { "status": Simulation.status(id).status_id }
