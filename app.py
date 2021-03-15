from flask import Flask
from stochss_remote.api.v1.job import blueprint

app = Flask(__name__)
app.register_blueprint(blueprint)

# from stochss_remote.job_manager import SimulationJob
# job = SimulationJob("gillespy2", "1.5.7")