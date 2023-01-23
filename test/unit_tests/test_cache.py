'''
test.unit_tests.test_cache
'''
import os
import subprocess
import unittest
from gillespy2 import Model
from stochss_compute.core.messages import SimulationRunRequest
from stochss_compute.server.cache import Cache
from . import gillespy2_models


class CacheTest(unittest.TestCase):
    '''
    Test cache functioniality.
    '''
    cache_dir = 'cache'
    def setUp(self) -> None:
        if os.path.exists(self.cache_dir):
            rm = subprocess.Popen(['rm', '-r', self.cache_dir])
            rm.wait()

    def tearDown(self) -> None:
        if os.path.exists(self.cache_dir):
            rm = subprocess.Popen(['rm', '-r', self.cache_dir])
            rm.wait()

    def test_cache(self):
        '''
        Tests: 
            exists()
            is_empty()
            n_traj_needed()
            is_ready()
            create()
            save()
        '''
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                print(f'test_cache():{create_model}')
                if create_model in ('create_oregonator','create_lac_operon', 'create_decay_no_tspan'):
                    print('SKIP')
                    continue
                model: Model = gillespy2_models.__dict__[create_model]()
                sim_request = SimulationRunRequest(model)
                cache = Cache(cache_dir=self.cache_dir, results_id=sim_request.hash())
                assert cache.exists() is False
                assert cache.is_empty() is True
                assert cache.n_traj_needed(0) == 0
                assert cache.n_traj_needed(1) == 1
                assert cache.n_traj_in_cache() == 0
                results = model.run()
                cache.create()
                cache.save(results)
                assert cache.exists() is True
                assert cache.is_empty() is False
                assert cache.n_traj_in_cache() == 1
                results_get = cache.get()
                assert len(results_get) == 1
                assert cache.n_traj_needed(2) == 1
                assert cache.is_ready(2) is False
                assert cache.is_ready(1) is True
                results = model.run()
                cache.create()
                cache.save(results)
                assert len(cache.get()) == 2
                assert cache.n_traj_needed(3) == 1
                assert cache.n_traj_needed(2) == 0
                assert cache.n_traj_needed(1) == 0
                assert cache.is_ready(3) is False
                assert cache.is_ready(2) is True
