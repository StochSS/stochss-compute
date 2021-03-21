import base64, dill

def into_pickle(data):
    return base64.b64encode(dill.dumps(data)).decode("ascii")

def from_pickle(data):
    return dill.loads(base64.b64decode(data))