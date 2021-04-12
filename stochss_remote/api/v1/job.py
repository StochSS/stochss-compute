import json

from threading import Thread
from flask import Blueprint, request, jsonify, make_response
from gillespy2.core.jsonify import TranslationTable
from gillespy2.solvers.cpp.ssa_c_solver import SSACSolver

from stochss_remote.api import request_helpers
from stochss_remote.api.job_manager import JobManager
from stochss_remote.api.simulation import Simulation
from gillespy2.core import Model

blueprint = Blueprint("job", __name__, url_prefix="/job")
job_manager = JobManager()

@blueprint.route("/create", methods = [ "POST" ])
def create():
    sim = request.args.get("sim", default = "gillespy2", type = str)
    version = request.args.get("version", default = "", type = str)

    sim = Simulation(sim, version)
    job_manager.add(sim)

    return make_response(jsonify({ "job": f"/job/{sim.id}" }), 202)

@blueprint.route("/<string:id>", methods = [ "GET" ])
def status(id):
    job = job_manager.get(id)

    if job == None:
        return make_response(jsonify({ "message": f"A job with id: {id} does not exist." }), 404)

    return make_response(jsonify({
        "id": id,
        "status": str(job.status)
    }))

@blueprint.route("/<string:id>/start", methods = [ "POST" ])
def start(id):
    job = job_manager.get(id)

    if job == None:
        return make_response(jsonify({ "message": f"A job with id: {id} does not exist." }), 404)

    request_json = request.get_json()

    params = json.loads(request_json["params"])
    model = Model.from_json(request_json["model"])

    result = model.run()
    return make_response(result.to_json(), 202)

