import requests, json, time
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

        model = self.model.to_anon()
        model_hash = model.get_json_hash()

        request_json = {
            "type": "gillespy2",
            "hash": model_hash,
            "model": model.to_json()
        }

        result = requests.post(f"{self.server.address}/v1/job/start", json=request_json)
        status_url  = f"{self.server.address}{result.json()['status']}"
        status = requests.get(status_url).json()

        while status["status_id"] != "SUCCESS":
            time.sleep(5)
            status = requests.get(status_url).json()

        return Results.from_json(status["results"])

class ComputeServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = f"http://{host}:{port}"