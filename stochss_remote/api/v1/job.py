import multiprocessing

from threading import Thread
from flask import Flask, Blueprint, request, jsonify, make_response
from stochss_remote.job_manager import SimulationJob, jobs, install

blueprint = Blueprint("job", __name__, url_prefix="/job")

@blueprint.route("/create")
def create():
    sim = request.args.get("sim", default = "gillespy2", type = str)
    version = request.args.get("version", default = "", type = str)

    job = SimulationJob(sim, version)

    thread = Thread(target = install, args = (job.id,))
    thread.start()

    # process = multiprocessing.Process(target = install, args = (job.id,))
    # process.start()

    return make_response(jsonify({ "job": f"/job/{job.id}" }), 202)

@blueprint.route("/<string:id>", methods = [ "GET" ])
def status(id):
    if jobs[id] == None:
        return make_response(jsonify({ "message": f"A job with id: {id} does not exist." }), 404)

    return make_response(jsonify({
        "id": id,
        "status": str(jobs[id].status)
    }))
