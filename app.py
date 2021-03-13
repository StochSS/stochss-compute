from flask import Flask
from stochss_remote.api import v1

#app = Flask(__name__)
#app.register_blueprint(v1.job.blueprint)

from stochss_remote.job_manager import SimulationJob
job = SimulationJob("gillespy2", "1.5.7")