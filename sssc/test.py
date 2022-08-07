import json
import gillespy2
import numpy
import tornado.escape
from messages import SimulationRunRequest
from tornado.httpclient import HTTPRequest
from tornado.httpclient import HTTPClient, AsyncHTTPClient
import requests
url = 'http://localhost:29681/run'
class MichaelisMenten(gillespy2.Model):
     def __init__(self, parameter_values=None):
            #initialize Model
            gillespy2.Model.__init__(self, name="Michaelis_Menten")
            rate1 = gillespy2.Parameter(name='rate1', expression= 0.0017)
            self.add_parameter([rate1])
            A = gillespy2.Species(name='A', initial_value=301)
            self.add_species([A])
            self.timespan(numpy.linspace(0,1000,101))
model = MichaelisMenten()
request = SimulationRunRequest(model, 'SSA')
test = {
        'test': 'test'
}
request_json = tornado.escape.json_encode(test)
print(type(request_json))
response = requests.post(url, json=request.__dict__ )
print(response.text)