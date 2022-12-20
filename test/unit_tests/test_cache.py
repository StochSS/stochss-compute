import os
import subprocess
import unittest

import gillespy2_models
from gillespy2 import Model, ODESolver

from stochss_compute.core.messages import SimulationRunRequest
from stochss_compute.server.cache import Cache

class CacheTest(unittest.TestCase):
    cache_dir = 'cache'

    @classmethod
    def setUpClass(cls) -> None:
        if os.path.exists(cls.cache_dir):
            subprocess.Popen(['rm', '-r', cls.cache_dir])
        if not os.path.exists(cls.cache_dir):
            subprocess.Popen(['mkdir', cls.cache_dir])
        
    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.cache_dir):
            subprocess.Popen(['rm', '-r', cls.cache_dir])

    def test_cache(self):
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                print(f'test_cache():{create_model}')
                if create_model in ('create_oregonator','create_lac_operon', 'create_decay_no_tspan'):
                    print('SKIP')
                    continue
                model: Model = gillespy2_models.__dict__[create_model]()
                sim_request = SimulationRunRequest(model)
                cache = Cache(cache_dir='cache', results_id=sim_request._hash())
                assert(cache.exists() == True, 'hi')
                assert(cache.is_empty() == True)
                results = model.run()
                cache.new(results)
                assert(cache.exists() == True)
                assert(cache.is_empty() == False)
                results_get = cache.get()
                assert(len(results_get) == 1)

