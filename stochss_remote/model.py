import json, base64, requests, dill

def connect_to(host, port):
    return RemoteModel(host, port)

class ComputeServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"

    def with_model(self, model):
        self.model = model
        self.model_encoded = base64.b64encode(dill.dumps(self.model))

        return self

    def run(self, **params):
        test = dict(params)

        create_req = requests.post(f"{self.address}/job/create", json = { "sim": "gillespy2", "version": "1.5.7" })
        status_addr = create_req.json()["job"]

        status = requests.get(f"{self.address}{status_addr}")
        id = status.json()["id"]

        result = requests.post(f"{self.address}/job/{id}/start", json = { "params": json.dumps(dict(params)), "model": self.model_encoded.decode("ascii") })
    
        return dill.loads(result.content)
