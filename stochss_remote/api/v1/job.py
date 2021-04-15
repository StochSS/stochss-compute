from flask_restx import reqparse
from flask_restx import Namespace, Resource
from celery.states import SUCCESS

from ..simulation import Simulation

api = Namespace("Job API", "Endpoint to control the creation, execution, and deletion of running jobs.", path="/job")

@api.route("/create")
class Create(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("sim", type=str, required=True, help="The name of the simulation to be associated with this job.")
    parser.add_argument("hash", type=str, required=True, help="The hash of the model to be run.")

    def post(self):
        args = self.parser.parse_args()
        id = Simulation(args["type"], args["hash"], args["model"], args["param"]).run()

@api.route("/start")
class Start(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("type", type=str, required=True, help="The type of simulation to be associated with this job.")
    parser.add_argument("hash", type=str, required=True, help="The hash of the model to be run.")
    parser.add_argument("model", type=str, required=True, help="The model to be run.")
    parser.add_argument("params", type=str, required=False, help="Model run parameters.")
    
    def post(self):
        args = self.parser.parse_args()
        id = Simulation(args["type"], args["hash"], args["model"], args["params"]).run()

        return { "status": f"/v1/job/status/{id}" }

@api.route("/status/<string:id>")
class Status(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("id", type=str, required=True, help="The ID of the job.")

    def get(self, id):
        status = Simulation.status(id)

        if status == SUCCESS:
            return {
                "status": status,
                "results": Simulation.result(id)
            }

        return { "status": Simulation.status(id) }