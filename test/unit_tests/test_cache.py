import os
import subprocess
import unittest

from test.unit_tests import gillespy2_models
from gillespy2 import Model

from stochss_compute.core.messages import SimulationRunRequest
from stochss_compute.server.cache import Cache

class CacheTest(unittest.TestCase):
    cache_dir = 'cache'
    def setUp(self) -> None:
        if os.path.exists(self.cache_dir):
            subprocess.Popen(['rm', '-r', self.cache_dir])
        if not os.path.exists(self.cache_dir):
            subprocess.Popen(['mkdir', self.cache_dir])
        
    def tearDown(self) -> None:
        if os.path.exists(self.cache_dir):
            subprocess.Popen(['rm', '-r', self.cache_dir])

    def test_cache(self):
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                print(f'test_cache():{create_model}')
                if create_model in ('create_oregonator','create_lac_operon', 'create_decay_no_tspan'):
                    print('SKIP')
                    continue
                model: Model = gillespy2_models.__dict__[create_model]()
                sim_request = SimulationRunRequest(model)
                cache = Cache(cache_dir=self.cache_dir, results_id=sim_request._hash())
                assert(cache.exists() == False)
                assert(cache.is_empty() == True)
                results = model.run()
                cache.save(results)
                assert(cache.exists() == True)
                assert(cache.is_empty() == False)
                results_get = cache.get()
                assert(len(results_get) == 1)
                assert cache.n_traj_needed(2) == 1
                assert cache.is_ready(2) == False
                assert cache.is_ready(1) == True
                results = model.run()
                cache.save(results)
                assert len(cache.get()) == 2
                assert cache.n_traj_needed(3) == 1
                assert cache.n_traj_needed(2) == 0
                assert cache.n_traj_needed(1) == 0
                assert cache.is_ready(3) == False
                assert cache.is_ready(2) == True


