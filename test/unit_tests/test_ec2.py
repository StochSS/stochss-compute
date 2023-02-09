'''
test.unit_tests.test_launch
'''
import os
import unittest
from moto import mock_ec2
from stochss_compute.cloud import EC2Cluster, EC2LocalConfig #, EC2RemoteConfig

class MockEC2(EC2Cluster):
    def _poll_launch_progress(self, container_names):
        return super()._poll_launch_progress(container_names, mock=True)
    def _get_source_ip(self, cloud_key):
        return 'localhost'
    def _restrict_ingress(self, ip_address: str = ''):
        try:
            super()._restrict_ingress(ip_address)
        except NotImplementedError as oh_well:
            print(oh_well)

@mock_ec2
class EC2ClusterTest(unittest.TestCase):
    '''
    Test EC2Cluster class.
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
        self.cluster.clean_up()
        return super().tearDown()
    
    def test_init(self):
        '''
        Tests init.
        '''
        assert self.cluster is not None

    def test_launch(self):
        '''
        Tests init.
        '''
        self.cluster.launch_single_node_instance('t3.micro')
