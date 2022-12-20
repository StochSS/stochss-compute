import unittest

import gillespy2_models
from gillespy2 import Model

from stochss_compute.core.messages import SimulationRunRequest
from stochss_compute.server.cache import Cache

class CacheTest(unittest.TestCase):

    def test_cache(self):
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                model: Model = gillespy2_models.__dict__[create_model]()
                sim_request = SimulationRunRequest(model)
                results = model.run()
                results = model.run(number_of_trajectories=1)
                results = model.run(number_of_trajectories=2)
                results = model.run(number_of_trajectories=1)
                cache = Cache(cache_dir='cache', results_id=sim_request1._hash())

                if cache.is_empty():
                    cache.get()

                assert(sim_request1._hash() == sim_request2._hash())

