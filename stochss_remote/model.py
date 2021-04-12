import requests, json

from stochss_remote.api import request_helpers
from gillespy2.core import Model, Results

def connect_to(host, port):
    return RemoteSimulation(host, port)

class RemoteSimulation():
    def on(server):
        sim = RemoteSimulation()
        sim.server = server

        return sim

    def with_model(self, model):
        self.model = model

        return self

    def run(self, **params):
        params = json.dumps(params)

        translation_table = self.model.get_translation_table()

        create_req = requests.post(f"{self.server.address}/job/create", json = { "sim": "gillespy2", "version": "1.5.7" })
        status_addr = create_req.json()["job"]

        status = requests.get(f"{self.server.address}{status_addr}")
        id = status.json()["id"]

        request_json = {
            "params": params,
            "model": self.model.to_anon().to_json()
        }

        result = requests.post(f"{self.server.address}/job/{id}/start", json = request_json)
        result = Results.from_json(result.content.decode())
        result.translation_table = translation_table

        print(result)

        return result.to_named()

class ComputeServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = f"http://{host}:{port}"