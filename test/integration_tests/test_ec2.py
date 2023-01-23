'''
test.integration_tests.test_api
'''
import os
import subprocess
import time
import unittest
import mockssh
from moto import mock_ec2

from stochss_compute import EC2Cluster, RemoteSimulation, EC2LocalConfig, EC2RemoteConfig


from .gillespy2_models import create_michaelis_menten

@mock_ec2
class EC2Test(unittest.TestCase):
    '''
    Spins up a mock ec2 instance for testing.
    '''

    # @classmethod
    # def setUpClass(cls) -> None:

    #     time.sleep(3)

    # @classmethod
    # def tearDownClass(cls) -> None:
    #     cls.api_server.terminate()
    #     cls.api_server.wait()

    # def tearDown(self) -> None:
    #     for filename in os.listdir('cache'):
    #         os.remove(f'cache/{filename}')
    #     return super().tearDown()
    def _launch_single_node_instance(self, cluster, instance_type):
        """
        Launches a single node StochSS-Compute instance. Make sure to check instance_type pricing before launching.

        :param instance_type: Example: 't3.nano' See full list here: https://aws.amazon.com/ec2/instance-types/
        :type instance_type: str
         """

        cluster._set_status('launching')
        cluster._launch_network()
        cluster._create_root_key()
        users = {
            "ec2-user": ".sssc/sssc-server-ssh-key.pem",
        }
        with mockssh.Server(users):
            cluster._launch_head_node(instance_type=instance_type)
            cluster._set_status(cluster._server.state['Name'])

    def test_run_resolve(self):
        '''
        Basic function.
        '''
        with mock_ec2():
            os.environ["AWS_ACCESS_KEY_ID"] = "testing"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
            os.environ["AWS_SECURITY_TOKEN"] = "testing"
            os.environ["AWS_SESSION_TOKEN"] = "testing"
            local_config = EC2LocalConfig()
            cluster = EC2Cluster(local_config=local_config)
            self._launch_single_node_instance(cluster, 't3.nano')
            model = create_michaelis_menten()
            sim = RemoteSimulation(model, cluster)
            results = sim.run()
            assert results.data is not None

    def _launch_head_node(self, instance_type):
        """
        Launches a StochSS-Compute server instance.
        """
        cloud_key = token_hex(32)

        launch_commands = f'''#!/bin/bash
sudo yum update -y
sudo yum -y install docker
sudo usermod -a -G docker ec2-user
sudo service docker start
sudo chmod 666 /var/run/docker.sock 
docker run --network host --rm -t -e CLOUD_LOCK={cloud_key} --name sssc stochss/stochss-compute:cloud stochss-compute-cluster -p {self._remote_config.api_port} > /home/ec2-user/sssc-out 2> /home/ec2-user/sssc-err &
'''
        kwargs = {
            'ImageId': self._ami,
            'InstanceType': instance_type,
            'KeyName': self._remote_config.key_name,
            'MinCount': 1,
            'MaxCount': 1,
            'SubnetId': self._subnets['public'].id,
            'SecurityGroupIds': [self._default_security_group.id, self._server_security_group.id],
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._remote_config.server_name
                        },
                    ]
                },
            ],
            'UserData': launch_commands,
        }

        self.log.info(
            'Launching StochSS-Compute server instance. This might take a minute.......')
        try:
            response = self._client.run_instances(**kwargs)
        except ClientError as c_e:
            raise EC2Exception from c_e

        instance_id = response['Instances'][0]['InstanceId']
        # try catch
        self._server = self._resources.Instance(instance_id)
        self._server.wait_until_exists()
        self._server.wait_until_running()

        self.log.info('Instance "%s" is running.', instance_id)

        self._poll_launch_progress(['sssc'])

        self.log.info('Restricting server access to only your ip.')
        source_ip = self._get_source_ip(cloud_key)

        self._restrict_ingress(source_ip)
        self._init = True
        self.log.info('StochSS-Compute ready to go!')

    def _poll_launch_progress(self, container_names):
        """
        Polls the instance to see if the Docker container is running.

        :param container_names: A list of Docker container names to check against.
        :type container_names: List[str]
        """
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        sshtries = 0
        while True:
            try:
                ssh.connect(self._server.public_ip_address, username='ec2-user',
                            key_filename=self._local_config.key_path, look_for_keys=False)
                break
            except Exception as err:
                if sshtries >= 5:
                    raise err
                self._server.reload()
                sleep(5)
                sshtries += 1
                continue
        for container in container_names:
            sshtries = 0
            while True:
                sleep(60)
                _, stdout, stderr = ssh.exec_command(
                    "docker container inspect -f '{{.State.Running}}' " + f'{container}')
                rc = stdout.channel.recv_exit_status()
                out = stdout.readlines()
                err2 = stderr.readlines()
                if rc == -1:
                    ssh.close()
                    raise EC2Exception(
                        "Something went wrong connecting to the server. No exit status provided by the server.")
                # Wait for yum update, docker install, container download
                if rc == 1 or rc == 127:
                    self.log.info('Waiting on Docker daemon.')
                    sshtries += 1
                    if sshtries >= 5:
                        ssh.close()
                        raise EC2Exception(
                            f"Something went wrong with Docker. Max retry attempts exceeded.\nError:\n{''.join(err2)}")
                if rc == 0:
                    if 'true\n' in out:
                        sleep(10)
                        self.log.info('Container "%s" is running.', container)
                        break
        ssh.close()
