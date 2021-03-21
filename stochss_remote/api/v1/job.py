import multiprocessing

from threading import Thread
from flask import Flask, Blueprint, request, jsonify, make_response
from stochss_remote.api.job_manager import Simulation, JobManager

blueprint = Blueprint("job", __name__, url_prefix="/job")

@blueprint.route("/create", methods = [ "POST" ])
def create():
    sim = request.args.get("sim", default = "gillespy2", type = str)
    version = request.args.get("version", default = "", type = str)

    sim = Simulation(sim, version)
    JobManager.add(sim)

    return make_response(jsonify({ "job": f"/job/{sim.id}" }), 202)

@blueprint.route("/<string:id>", methods = [ "GET" ])
def status(id):
    job = JobManager.get(id)

    if job == None:
        return make_response(jsonify({ "message": f"A job with id: {id} does not exist." }), 404)

    return make_response(jsonify({
        "id": id,
        "status": str(job.status)
    }))

@blueprint.route("/<string:id>/start")
def start(id):
    job = JobManager.get(id)

    if job == None:
        return make_response(jsonify({ "message": f"A job with id: {id} does not exist." }), 404)

