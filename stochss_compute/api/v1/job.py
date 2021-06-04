from gillespy2 import Model
from flask.views import MethodView

from stochss_compute.api import delegate
from stochss_compute.api.delegate.delegate import JobState

class Create(MethodView):
    parser = reqparse.RequestParser()
    parser.add_argument("sim", type=str, required=True, help="The name of the simulation to be associated with this job.")
    parser.add_argument("hash", type=str, required=True, help="The hash of the model to be run.")

    def post(self):
        args = self.parser.parse_args()
        id = Simulation(args["type"], args["hash"], args["model"], args["param"]).run()

class Start(MethodView):
    parser = reqparse.RequestParser()

    parser.add_argument("type", type=str, required=True, help="The type of simulation to be associated with this job.")
    parser.add_argument("hash", type=str, required=True, help="The hash of the model to be run.")
    parser.add_argument("model", type=str, required=True, help="The model to be run.")
    parser.add_argument("params", type=str, required=False, help="Model run parameters.")
    
    def post(self):
        args = self.parser.parse_args()

        delegate.start_job()
        id = Simulation(args["type"], args["hash"], args["model"], args["params"]).run()

        return { "status": f"/v1/job/status/{id}" }

class Status(MethodView):
    parser = reqparse.RequestParser()
    parser.add_argument("id", type=str, required=True, help="The ID of the job.")

    def get(self, id):
        status = Simulation.status(id)

        if status.status_id == JobState.SUCCESS:
            return {
                "status_id": status.status_id,
                "status_text": status.status_text,
                "results": Simulation.result(id)
            }

        return { "status": Simulation.status(id).status_id }