from stochss_compute import RemoteSimulation, ComputeServer
from stochss_compute.compute_server import Endpoint
from .api import SourceIpRequest, SourceIpResponse
from ..remote_utils import unwrap_or_err
from .exceptions import ResourceException

from gillespy2 import Model

import boto3
from botocore.exceptions import ClientError
from paramiko import SSHClient, AutoAddPolicy

import os
from time import sleep
from secrets import token_hex

_VPC_NAME = 'sssc-vpc'
_SUBNET_NAME = 'sssc-subnet'
_SECURITY_GROUP_NAME = 'sssc-sg'
_SERVER_NAME = 'sssc-server'
_SCHEDULER_NAME = 'sssc-scheduler'
_WORKER_PREFIX = 'sssc-worker-'
_KEY_NAME = 'sssc-root'
_KEY_PATH = './sssc-root.pem'
_API_PORT = 29681
_SSSC_AMI = 'ami-04268eeed853eaa55'

class Cluster():

    _client = boto3.client('ec2')
    _resources = boto3.resource('ec2')
    _restricted: bool = False
    _subnet = None
    _security_group = None
    _vpc = None
    _server = None
    _scheduler = None
    _workers = []

    def __init__(self) -> None:
        """ 
        Attempts to load a StochSS-Compute cluster.
         """
        try:
            self._load_cluster()
        except ResourceException:
            print('Misconfigured cluster detected. Cleaning up.')
            self.clean_up()
            print('StochSS-Compute ready to re-launch.')

    def clean_up(self):
        """ 
        Deletes all cluster resources.
         """
        vpc_search_filter = [
            {
                'Name': 'tag:Name',
                'Values': [
                    'sssc-vpc'
                ]
            }
        ]
        # 
        vpc_response = self._client.describe_vpcs(Filters=vpc_search_filter)
        if len(vpc_response['Vpcs']) != 0:
            vpc = self._vpc
            for instance in vpc.instances.all():
                instance.terminate()
                print(f'Terminating "{instance.id}". This might take a minute.......')
                instance.wait_until_terminated()
                self._server = None
                # self._scheduler = None
                # self._workers = []
                print(f'Instance {instance.id}" terminated.')
            for sg in vpc.security_groups.all():
                if sg.group_name == 'sssc-sg':
                    print(f'Deleting {sg.id}.......')
                    sg.delete()
                    self._security_group = None
                    print(f'Security group {sg.id} deleted.')
            for subnet in vpc.subnets.all():
                print(f'Deleting {subnet.id}.......')
                subnet.delete()
                self._subnet = None
                print(f'Subnet {subnet.id} deleted.')
            for igw in vpc.internet_gateways.all():
                print(f'Detaching {igw.id}.......')
                igw.detach_from_vpc(VpcId=vpc.vpc_id)
                print(f'Gateway {igw.id} detached.')
                print(f'Deleting {igw.id}.......')
                igw.delete()
                print(f'Gateway {igw.id} deleted.')
            print(f'Deleting {vpc.id}.......')
            vpc.delete()
            self._vpc = None
            print(f'VPC {vpc.id} deleted.')
        key_pair = self._resources.KeyPair(_KEY_NAME)
        print(f'Deleting "{_KEY_NAME}".')
        key_pair.delete()
        print(f'Key Pair "{_KEY_NAME}" deleted.')
        self._delete_root_key()
        
    def _create_root_key(self):
        """ 
        Creates a key pair for SSH login and instance launch.
        """
        keyType='ed25519'
        keyFormat='pem'

        response = self._client.create_key_pair(KeyName=_KEY_NAME, KeyType=keyType, KeyFormat=keyFormat)

        waiter = self._client.get_waiter('key_pair_exists')
        waiter.wait(KeyNames=[_KEY_NAME])

        key = open(_KEY_PATH, 'x')
        key.write(response['KeyMaterial'])
        key.close()
        os.chmod(_KEY_PATH, 0o400)

    def _delete_root_key(self) -> None:
        f"""
        Deletes {_KEY_PATH} if it exists. 
        """
        if os.path.exists(_KEY_PATH):
            print(f'Deleting "{_KEY_PATH}".')
            os.remove(_KEY_PATH)
            print(f'Root key deleted.')

    def _create_sssc_vpc(self):
        f"""
        Creates a vpc named {_VPC_NAME}. 
        """
        vpc_cidrBlock = '172.31.0.0/16'
        vpc_tag = [
            {
                'ResourceType': 'vpc',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': _VPC_NAME
                    }
                ]
            }
        ]

        vpc_response = self._client.create_vpc(CidrBlock=vpc_cidrBlock, TagSpecifications=vpc_tag)
        vpc_id = vpc_response['Vpc']['VpcId']
        vpc_waiter = self._client.get_waiter('vpc_available')
        vpc_waiter.wait(VpcIds=[vpc_id])
        self._vpc = self._resources.Vpc(vpc_id)

        self._client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsSupport={'Value': True})
        self._client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsHostnames={'Value': True})

        igw_response = self._client.create_internet_gateway()
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        igw_waiter = self._client.get_waiter('internet_gateway_exists')
        igw_waiter.wait(InternetGatewayIds=[igw_id])
        
        self._vpc.attach_internet_gateway(InternetGatewayId=igw_id)
        for rtb in self._vpc.route_tables.all():
            if rtb.associations_attribute[0]['Main'] == True:
                rtb_id = rtb.route_table_id
        self._client.create_route(RouteTableId=rtb_id, GatewayId=igw_id, DestinationCidrBlock='0.0.0.0/0')

        self._vpc.reload()

    def _create_sssc_subnet(self):
        f""" 
        Creates a subnet named {_SUBNET_NAME}.
        """
        subnet_cidrBlock = '172.31.0.0/20'
        subnet_tag = [
            {
                'ResourceType': 'subnet',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': _SUBNET_NAME
                    }
                ]
            }
        ]
        self._subnet = self._vpc.create_subnet(CidrBlock=subnet_cidrBlock, TagSpecifications=subnet_tag)
        waiter = self._client.get_waiter('subnet_available')
        waiter.wait(SubnetIds=[self._subnet.id])

        self._client.modify_subnet_attribute(SubnetId=self._subnet.id, MapPublicIpOnLaunch={'Value': True})
        self._subnet.reload()

    def _create_sssc_security_group(self):
        f"""
        Creates a security group named {_SECURITY_GROUP_NAME} for SSH and StochSS-Compute API access.
        """
        description = 'Default Security Group for StochSS-Compute.'
        self._security_group = self._vpc.create_security_group(Description=description, GroupName=_SECURITY_GROUP_NAME)
        sshargs = {
            'CidrIp': '0.0.0.0/0',
            'FromPort': 22,
            'ToPort': 22,
            'IpProtocol': 'tcp',
        }
        self._security_group.authorize_ingress(**sshargs)
        sgargs = {
            'CidrIp': '0.0.0.0/0',
            'FromPort': _API_PORT,
            'ToPort': _API_PORT,
            'IpProtocol': 'tcp',
            'TagSpecifications': [
                {
                    'ResourceType': 'security-group-rule',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'api-server'
                        },
                    ]
                },
            ]
        }
        self._security_group.authorize_ingress(**sgargs)
        self._security_group.reload()

    def _restrict_ingress(self, ipAddress: str = ''):
        """ 
        Modifies the security group API ingress rule to only allow access on port 29681 from the given ip address.
         """
        ruleFilter=[
            {
                'Name': 'group-id',
                'Values': [
                    self._security_group.id,
                ]
            },
            {
                'Name': 'tag:Name',
                'Values': [
                    'api-server',
                ]
            },
        ]
        sgr_response = self._client.describe_security_group_rules(Filters=ruleFilter)
        sgr_id = sgr_response['SecurityGroupRules'][0]['SecurityGroupRuleId']
        newSecurityGroupRules=[
            {
                'SecurityGroupRuleId': sgr_id,
                'SecurityGroupRule': {
                    'IpProtocol': 'tcp',
                    'FromPort': _API_PORT,
                    'ToPort': _API_PORT,
                    'CidrIpv4': f'{ipAddress}/32',
                    'Description': 'Restricts cluster access.'
                }
            },
        ]
        self._client.modify_security_group_rules(GroupId=self._security_group.id, SecurityGroupRules=newSecurityGroupRules)
        self._security_group.reload()

    def _launch_network(self):
        """ 
        Launches required network resources.
         """
        print("Launching Network.......")
        self._create_sssc_vpc()
        self._create_sssc_subnet()
        self._create_sssc_security_group()

    def _launch_server(self, instanceType='t3.micro'):
        """ 
        Launches a StochSS-Compute server instance. On
         """
        cloud_key = token_hex(32)

        launch_commands = f'''#!/bin/bash
sudo service docker start
docker run --network host --rm -e CLOUD_LOCK={cloud_key} --name sssc stochss/stochss-compute:cloud > /home/ec2-user/sssc-out 2> /home/ec2-user/sssc-err
'''
        kwargs = {
            'ImageId': _SSSC_AMI, 
            'InstanceType': instanceType,
            'KeyName': _KEY_NAME,
            'MinCount': 1, 
            'MaxCount': 1,
            'SubnetId': self._subnet.id,
            'SecurityGroupIds': [self._security_group.id],
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': _SERVER_NAME
                        },
                    ]
                },
            ],
            'UserData': launch_commands,
            }
        print(f'Launching StochSS-Compute server instance.......(This could take a minute)')
        response = self._client.run_instances(**kwargs)
        instance_id = response['Instances'][0]['InstanceId']
        self._server = self._resources.Instance(instance_id)
        self._server.wait_until_running()


        print(f'Instance "{instance_id}" is running.')

        self._poll_launch_progress()
        if self._restricted == False:
            print('Restricting server access to only your ip.')
            source_ip = self._get_source_ip(cloud_key)
            self._restrict_ingress(source_ip)
            self._restricted = True
        print('StochSS-Compute ready to go!')
        return self._server

    def _poll_launch_progress(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        sshtries = 0
        while True:
            try:
                ssh.connect(self._server.public_ip_address, username='ec2-user', key_filename=_KEY_PATH, look_for_keys=False)
                break
            except Exception as e:
                if sshtries >= 5:
                    raise e
                self._server.reload()
                sleep(5)
                sshtries += 1
                continue

        sshtries = 0
        while True:
            sleep(10)
            stdin,stdout,stderr = ssh.exec_command("docker container inspect -f '{{.State.Running}}' sssc")
            rc = stdout.channel.recv_exit_status()
            if rc == -1:
                ssh.close()
                raise Exception("Something went wrong connecting to the server. No exit status provided by the server.")
            if rc == 1 or rc == 127:
                print('Waiting on docker.')
                sshtries += 1
                if sshtries >= 5:
                    ssh.close()
                    raise Exception("Something went wrong with docker. Max retry attempts exceeded.")
            if rc == 0:
                out = stdout.readline()
                if out == 'true\n':
                    sleep(10)
                    print('StochSS-Compute is running.')
                    ssh.close()
                    break

        
    def _load_cluster(self, vpcId=None):
        '''
        Reload cluster resources. Returns False if no VPC named sssc-vpc.
        '''

        vpc_search_filter = [
            {
                'Name': 'tag:Name',
                'Values': [
                    _VPC_NAME
                ]
            }
        ]
        vpc_response = self._client.describe_vpcs(Filters=vpc_search_filter)
        if len(vpc_response['Vpcs']) == 0:
            return False
        if len(vpc_response['Vpcs']) == 2:
            print('More than one VPC named sssc-vpc.')
            raise ResourceException
        vpc_id = vpc_response['Vpcs'][0]['VpcId']
        self._vpc = self._resources.Vpc(vpc_id)
        vpc = self._vpc
        errors = False
        for instance in vpc.instances.all():
            for tag in instance.tags:
                if tag['Key'] == 'Name' and tag['Value'] == 'sssc-server':
                    self._server = instance
        if self._server is None:
            print('No instances named "sssc-server".')
            errors = True
        for sg in vpc.security_groups.all():
            if sg.group_name == 'sssc-sg':
                self._security_group = sg
        if self._security_group is None:
            print('No security group named "sssc-sg".')
            errors = True
        for subnet in vpc.subnets.all():
            for tag in subnet.tags:
                if tag['Key'] == 'Name' and tag['Value'] == 'sssc-subnet':
                    self._subnet = subnet
        if self._subnet is None:
            print('No subnet named "sssc-subnet".')
            errors = True
        if errors is True:
            raise ResourceException

    def _get_source_ip(self, cloud_key):
        ip = self._server.public_ip_address
        server = ComputeServer(ip, port=_API_PORT)
        source_ip_request = SourceIpRequest(cloud_key=cloud_key)
        source_ip_response = unwrap_or_err(SourceIpResponse, server.post(Endpoint.CLOUD, sub='/sourceip', request=source_ip_request))
        return source_ip_response.source_ip

    def launch_single_node_cluster(self):
        self._launch_network()
        self._create_root_key()
        self._launch_server()

    def run(self, model: Model):
        ip = self._server.public_ip_address
        server = ComputeServer(ip, port=_API_PORT)
        return RemoteSimulation.on(server).with_model(model).run()
