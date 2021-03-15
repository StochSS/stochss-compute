import multiprocessing

from flask import Flask, Blueprint, request, jsonify
from stochss_remote.job_manager import SimulationJob

blueprint = Blueprint("job", __name__, url_prefix="/job")

@blueprint.route("/create")
def create():
    sim = request.args.get("sim", default = "gillespy2", type = str)
    version = request.args.get("version", default = "", type = str)

    job = SimulationJob(sim, version)

    process = multiprocessing.Process(target = job.install)
    process.start()

    return jsonify(job.id)

@blueprint.route("/{id}")
def status(id):
    pass
