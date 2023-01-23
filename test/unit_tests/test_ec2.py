'''
test.unit_tests.test_launch
'''
import unittest
from stochss_compute.cloud import EC2Cluster, EC2LocalConfig, EC2RemoteConfig


class EC2ClusterTest(unittest.TestCase):
    '''
    Test ComputeServer class.
    '''

    def test_init(self):
        '''
        Tests init.
        '''
        cluster = EC2Cluster.__init__()
