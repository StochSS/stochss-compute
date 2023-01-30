'''
test.unit_tests.test_launch
'''
import unittest
from moto import mock_ec2
from stochss_compute.cloud import EC2Cluster, EC2LocalConfig, EC2RemoteConfig

@mock_ec2
class EC2ClusterTest(unittest.TestCase):
    '''
    Test ComputeServer class.
    '''

    def test_init(self):
        '''
        Tests init.
        '''
        cluster = EC2Cluster()
        assert cluster is not None
