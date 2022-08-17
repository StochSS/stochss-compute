import gillespy2
import numpy

from remote_simulation import RemoteSimulation

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
simulation = RemoteSimulation(model=model, host='localhost')
results = simulation.run()
print(results)