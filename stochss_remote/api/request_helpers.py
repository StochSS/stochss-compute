import base64, dill, jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy

def into_pickle(data):
    # jsonpickle_numpy.register_handlers()
    # return jsonpickle.encode(data)

    dill.settings['recurse'] = True
    return base64.b64encode(dill.dumps(data)).decode("ascii")

def from_pickle(data):
    # jsonpickle_numpy.register_handlers()
    # return jsonpickle.decode(data)

    dill.settings['recurse'] = True
    return dill.loads(base64.b64decode(data))