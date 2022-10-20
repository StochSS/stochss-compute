from stochss_compute.client.server import Server
from stochss_compute.core.messages import SourceIpRequest, SourceIpResponse
from stochss_compute.cloud.exceptions import EC2ImportException, ResourceException
from stochss_compute.client.endpoint import Endpoint

try:
    import boto3
    from botocore.session import get_session
    from paramiko import SSHClient, AutoAddPolicy
except ImportError as err:
    raise EC2ImportException
import os
from time import sleep
from secrets import token_hex

_VPC_NAME = 'sssc-vpc'
_SUBNET_PREFIX = 'sssc-subnet-'
_SECURITY_GROUP_NAME = 'sssc-sg'
_SERVER_NAME = 'sssc-server'
_KEY_NAME = 'sssc-root'
_KEY_PATH = f'./{_KEY_NAME}.pem'
_API_PORT = 29681
_AMIS = {
    # 'us-east-1': 'ami-0ef9fe14ea1c5c979',
    'us-east-2': 'ami-07e25c5bf81f82a4d',
    # 'us-west-1': 'ami-0a8c547cd139d4672',
    # 'us-west-2': 'ami-0e385035e7d059820',
}

class Cluster(Server):

    _client = None
    _resources = None
    _restricted: bool = False
    _subnets = {
        'public': None,
        'private': None
    }
    _default_security_group = None
    _server_security_group = None
    _vpc = None
    _server = None
    _ami = None

    def __init__(self) -> None:
        """ 
        Attempts to load a StochSS-Compute cluster. Otherwise just initializes a new cluster.
         """
        self._client = boto3.client('ec2')
        self._resources = boto3.resource('ec2')
        region = get_session().get_config_variable('region')
        self._ami = _AMIS[region]
        self._load_cluster()

    @property
    def address(self):
        if self._server is None:
            raise Exception('No server found. First launch a cluster.')
        if self._server.public_ip_address is None:
            self._server.reload()
        if self._server.public_ip_address is None:
            raise Exception('No public address found.')

        return f'http://{self._server.public_ip_address}:{_API_PORT}'

    def launch_single_node_instance(self, instanceType):
        """ 
        Launches a single node StochSS-Compute instance.

        :param instanceType: Example: 't3.micro' See full list here: https://aws.amazon.com/ec2/instance-types/ 
        :type instanceType: str
         """
        self._launch_network()
        self._create_root_key()
        self._launch_head_node(instanceType=instanceType)

    def clean_up(self):
        """ 
        Deletes all cluster resources.
        """
        vpc_search_filter = [
            {
                'Name': 'tag:Name',
                'Values': [
                    _VPC_NAME
                ]
            }
        ]
        vpc_response = self._client.describe_vpcs(Filters=vpc_search_filter)
        for vpc_dict in vpc_response['Vpcs']:
            vpc_id = vpc_dict['VpcId']
            vpc = self._resources.Vpc(vpc_id)
            for instance in vpc.instances.all():
                instance.terminate()
                print(f'Terminating "{instance.id}". This might take a minute.......')
                instance.wait_until_terminated()
                self._server = None
                print(f'Instance {instance.id}" terminated.')
            for sg in vpc.security_groups.all():
                if sg.group_name == _SECURITY_GROUP_NAME:
                    print(f'Deleting {sg.id}.......')
                    sg.delete()
                    self._server_security_group = None
                    print(f'Security group {sg.id} deleted.')
                elif sg.group_name == 'default':
                    self._default_security_group = None
            for subnet in vpc.subnets.all():
                print(f'Deleting {subnet.id}.......')
                subnet.delete()
                self._subnets['public'] = None
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
        try:
            self._client.describe_key_pairs(KeyNames=[_KEY_NAME])
            key_pair = self._resources.KeyPair(_KEY_NAME)
            print(f'Deleting "{_KEY_NAME}".')
            key_pair.delete()
            print(f'Key Pair "{_KEY_NAME}" deleted.')
        except:
            pass
        self._delete_root_key()

    def _launch_network(self):
        """ 
        Launches required network resources.
        """
        print("Launching Network.......")
        self._create_sssc_vpc()
        self._create_sssc_subnet(public=True)
        self._create_sssc_subnet(public=False)
        self._create_sssc_security_group()
        self._vpc.reload()

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
        vpc_waiter_exist = self._client.get_waiter('vpc_exists')
        vpc_waiter_exist.wait(VpcIds=[vpc_id])
        vpc_waiter_avail = self._client.get_waiter('vpc_available')
        vpc_waiter_avail.wait(VpcIds=[vpc_id])
        self._vpc = self._resources.Vpc(vpc_id)
        self._default_security_group = list(sg for sg in self._vpc.security_groups.all())[0]

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

    def _create_sssc_subnet(self, public: bool):
        f""" 
        Creates a public or private subnet prefixed {_SUBNET_PREFIX}.
        """
        if public is True:
            label = 'public'
            subnet_cidrBlock = '172.31.0.0/20'
        else:
            label = 'private'
            subnet_cidrBlock = '172.31.16.0/20'
        
        subnet_tag = [
            {
                'ResourceType': 'subnet',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': f'{_SUBNET_PREFIX}{label}'
                    }
                ]
            }
        ]
        self._subnets[label] = self._vpc.create_subnet(CidrBlock=subnet_cidrBlock, TagSpecifications=subnet_tag)
        waiter = self._client.get_waiter('subnet_available')
        waiter.wait(SubnetIds=[self._subnets[label].id])
        # if public is True:
        self._client.modify_subnet_attribute(SubnetId=self._subnets[label].id, MapPublicIpOnLaunch={'Value': True})
        self._subnets[label].reload()

    def _create_sssc_security_group(self):
        f"""
        Creates a security group named {_SECURITY_GROUP_NAME} for SSH and StochSS-Compute API access.
        """
        description = 'Default Security Group for StochSS-Compute.'
        self._server_security_group = self._vpc.create_security_group(Description=description, GroupName=_SECURITY_GROUP_NAME)
        sshargs = {
            'CidrIp': '0.0.0.0/0',
            'FromPort': 22,
            'ToPort': 22,
            'IpProtocol': 'tcp',
        }
        self._server_security_group.authorize_ingress(**sshargs)
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
        self._server_security_group.authorize_ingress(**sgargs)
        self._server_security_group.reload()

    def _restrict_ingress(self, ipAddress: str = ''):
        """ 
        Modifies the security group API ingress rule to only allow access on port 29681 from the given ip address.
        """
        ruleFilter=[
            {
                'Name': 'group-id',
                'Values': [
                    self._server_security_group.id,
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
        self._client.modify_security_group_rules(GroupId=self._server_security_group.id, SecurityGroupRules=newSecurityGroupRules)
        self._server_security_group.reload()

    def _launch_head_node(self, instanceType):
        """ 
        Launches a StochSS-Compute server instance.
        """
        cloud_key = token_hex(32)

        launch_commands = f'''#!/bin/bash
sudo service docker start
docker run --network host --rm -t -e CLOUD_LOCK={cloud_key} --name sssc stochss/stochss-compute:cloud > /home/ec2-user/sssc-out 2> /home/ec2-user/sssc-err &
'''
        kwargs = {
            'ImageId': self._ami, 
            'InstanceType': instanceType,
            'KeyName': _KEY_NAME,
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
                            'Value': _SERVER_NAME
                        },
                    ]
                },
            ],
            'UserData': launch_commands,
            }
        print(f'Launching StochSS-Compute server instance. This might take a minute.......')
        response = self._client.run_instances(**kwargs)
        instance_id = response['Instances'][0]['InstanceId']
        self._server = self._resources.Instance(instance_id)
        self._server.wait_until_exists()
        self._server.wait_until_running()

        print(f'Instance "{instance_id}" is running.')

        self._poll_launch_progress(['sssc'])

        print('Restricting server access to only your ip.')
        source_ip = self._get_source_ip(cloud_key)

        self._restrict_ingress(source_ip)
        print('StochSS-Compute ready to go!')

    def _poll_launch_progress(self, containerNames):
        """ 
        Polls the instance to see if the Docker container is running.

        :param containerNames: A list of Docker container names to check against.
        :type containerNames: List[str]
        """
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
        for container in containerNames:
            sshtries = 0
            while True:
                sleep(10)
                stdin,stdout,stderr = ssh.exec_command("docker container inspect -f '{{.State.Running}}' " + f'{container}')
                rc = stdout.channel.recv_exit_status()
                out = stdout.readlines()
                err = stderr.readlines()
                if rc == -1:
                    ssh.close()
                    raise Exception("Something went wrong connecting to the server. No exit status provided by the server.")
                if rc == 1 or rc == 127:
                    print('Waiting on Docker daemon.')
                    sshtries += 1
                    if sshtries >= 5:
                        ssh.close()
                        raise Exception(f"Something went wrong with Docker. Max retry attempts exceeded.\nError:\n{''.join(err)}")
                if rc == 0:
                    if 'true\n' in out:
                        sleep(10)
                        print(f'Container "{container}" is running.')
                        break
        ssh.close()

    def _get_source_ip(self, cloud_key):
        """
        Ping the server to find the IP address associated with the request.

        :param cloud_key: A secret key which must match the random key used to launch the instance.
        :type cloud_key: str
        """
        source_ip_request = SourceIpRequest(cloud_key=cloud_key)
        response_raw = self.post(Endpoint.CLOUD, sub='/sourceip', request=source_ip_request)
        if not response_raw.ok:
            raise Exception(response_raw.reason)
        response = SourceIpResponse.parse(response_raw.text)
        return response.source_ip

    def _load_cluster(self):
        '''
        Reload cluster resources. Returns False if no vpc named sssc-vpc.
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
            if os.path.exists(_KEY_PATH):
                raise ResourceException
            else:
                try:
                    self._client.describe_key_pairs(KeyNames=[_KEY_NAME]) 
                    raise ResourceException
                except:
                    pass              
            return False
        if len(vpc_response['Vpcs']) == 2:
            print(f'More than one VPC named "{_VPC_NAME}".')
            raise ResourceException
        vpc_id = vpc_response['Vpcs'][0]['VpcId']
        self._vpc = self._resources.Vpc(vpc_id)
        vpc = self._vpc
        errors = False
        for instance in vpc.instances.all():
            for tag in instance.tags:
                if tag['Key'] == 'Name' and tag['Value'] == _SERVER_NAME:
                    self._server = instance
        if self._server is None:
            print(f'No instances named "{_SERVER_NAME}".')
            errors = True
        for sg in vpc.security_groups.all():
            if sg.group_name == 'default':
                self._default_security_group = sg
            if sg.group_name == _SECURITY_GROUP_NAME:
                for rule in sg.ip_permissions:
                    if rule['FromPort'] == 29681 and rule['ToPort'] == 29681 and rule['IpRanges'][0]['CidrIp'] == '0.0.0.0/0':
                        errors = True
                self._server_security_group = sg
        if self._server_security_group is None:
            print(f'No security group named "{_SECURITY_GROUP_NAME}".')
            errors = True
        for subnet in vpc.subnets.all():
            for tag in subnet.tags:
                if tag['Key'] == 'Name' and tag['Value'] == f'{_SUBNET_PREFIX}public':
                    self._subnets['public'] = subnet
                if tag['Key'] == 'Name' and tag['Value'] == f'{_SUBNET_PREFIX}private':
                    self._subnets['private'] = subnet
        if None in self._subnets.values():
            print('Missing or misconfigured subnet.')
            errors = True
        if errors is True:
            raise ResourceException
        else:
            print('Cluster loaded.')
