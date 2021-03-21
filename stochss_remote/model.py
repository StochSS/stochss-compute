import json, base64, requests, dill
from stochss_remote.api import request_helpers

def connect_to(host, port):
    return RemoteModel(host, port)

class RemoteSimulation():
    def on(host, port):
        sim = RemoteSimulation()

        sim.host = host
        sim.port = port
        sim.address = f"{host}:{port}"

        return sim

    def with_model(self, model):
        self.model = model

        return self

    def run(self, **params):
        param_encoded = request_helpers.into_pickle(params)
        model_encoded = request_helpers.into_pickle(self.model)

        create_req = requests.post(f"{self.address}/job/create", json = { "sim": "gillespy2", "version": "1.5.7" })
        status_addr = create_req.json()["job"]

        status = requests.get(f"{self.address}{status_addr}")
        id = status.json()["id"]

        result = requests.post(f"{self.address}/job/{id}/start", json = { "params": param_encoded, "model": model_encoded })
    
        return request_helpers.from_pickle(result.content)
