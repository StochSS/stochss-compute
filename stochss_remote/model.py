import requests

def run(model, ip, port):
    address = f"{ip}:{port}"

    create_req = request.get(f"{address}/job/create")
    print("Hello world!")