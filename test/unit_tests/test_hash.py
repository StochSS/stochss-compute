import unittest

import test.unit_tests.gillespy2_models as gillespy2_models

from stochss_compute.core.messages import SimulationRunRequest

class HashTest(unittest.TestCase):

    def test_all_models(self):
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                model1 = gillespy2_models.__dict__[create_model]()
                model2 = gillespy2_models.__dict__[create_model]()
                sim_request1 = SimulationRunRequest(model1)
                sim_request2 = SimulationRunRequest(model2)

                assert(sim_request1._hash() == sim_request2._hash())

    def test_trajectories(self):
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                model1 = gillespy2_models.__dict__[create_model]()
                model2 = gillespy2_models.__dict__[create_model]()
                sim_request1 = SimulationRunRequest(model1)
                sim_request2 = SimulationRunRequest(model2, number_of_trajectories = 50)

                assert(sim_request1._hash() == sim_request2._hash())

