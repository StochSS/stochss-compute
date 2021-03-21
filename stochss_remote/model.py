import requests, base64, dill

def run(model, ip, port):
    address = f"{ip}:{port}"

    create_req = requests.post(f"{address}/job/create", data = { "sim": "gillespy2", "version": "1.5.7" })
    status_addr = create_req.json()["job"]

    status = requests.get(f"{address}{status_addr}")
    id = status.json()["id"]

    result = requests.post(f"{address}/job/{id}/start", data = dill.dumps(model))
   
    return dill.loads(result.content)
