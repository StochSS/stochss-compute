'''
HashTest(unittest.TestCase)
'''
import unittest
from stochss_compute.core.messages import SimulationRunRequest
from . import gillespy2_models

class HashTest(unittest.TestCase):
    '''
    Test SimulationRunRequest.hash()
    '''

    def test_all_models(self):
        '''
        Basic test on all example models
        '''
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                model1 = gillespy2_models.__dict__[create_model]()
                model2 = gillespy2_models.__dict__[create_model]()
                sim_request1 = SimulationRunRequest(model1)
                sim_request2 = SimulationRunRequest(model2)

                assert(sim_request1.hash() == sim_request2.hash())

    def test_trajectories(self):
        '''
        Test that all models hash correctly regardless of number_of_trajectories
        '''
        for create_model in gillespy2_models.__all__:
            with self.subTest(create_model=create_model):
                model1 = gillespy2_models.__dict__[create_model]()
                model2 = gillespy2_models.__dict__[create_model]()
                sim_request1 = SimulationRunRequest(model1)
                sim_request2 = SimulationRunRequest(model2, number_of_trajectories = 50)

                assert(sim_request1.hash() == sim_request2.hash())
