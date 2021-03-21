import json, base64, requests, dill
from stochss_remote.api import request_helpers

def connect_to(host, port):
    return RemoteModel(host, port)

class ComputeServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"

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
