'''
test.unit_tests.test_launch
'''
import unittest
from moto import mock_ec2
from stochss_compute.cloud import EC2Cluster, EC2LocalConfig, EC2RemoteConfig
import os

class MockEC2(EC2Cluster):
    def _poll_launch_progress(self, container_names):
        return super()._poll_launch_progress(container_names, mock=True)

@mock_ec2
class EC2ClusterTest(unittest.TestCase):
    '''
    Test ComputeServer class.
    '''
    cluster = None
    def setUp(self) -> None:
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        self.cluster = MockEC2(local_config=EC2LocalConfig(key_type='rsa'))
        return super().setUp()
    
    def tearDown(self) -> None:
        return super().tearDown()
    
    def test_init(self):
        '''
        Tests init.
        '''
        assert self.cluster is not None

    def test_(self):
        '''
        Tests init.
        '''
        self.cluster.launch_single_node_instance('t3.micro')
