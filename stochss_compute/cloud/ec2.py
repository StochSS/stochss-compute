from stochss_compute.client.server import Server
from stochss_compute.core.messages import SourceIpRequest, SourceIpResponse
from stochss_compute.cloud.exceptions import EC2ImportException, ResourceException, EC2Exception
from stochss_compute.client.endpoint import Endpoint
try:
    import boto3
    from botocore.session import get_session
    from botocore.exceptions import ClientError
    from paramiko import SSHClient, AutoAddPolicy
except ImportError as err:
    raise EC2ImportException
import os
import logging
from time import sleep
from secrets import token_hex

def _ec2Logger():
    log = logging.getLogger("EC2Cluster")
    log.setLevel(logging.INFO)
    log.propagate = False

    if not log.handlers:
        _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        _handler = logging.StreamHandler()
        _handler.setFormatter(_formatter)
        log.addHandler(_handler)
    
    return log

_VPC_NAME = 'sssc-vpc'
_SUBNET_PREFIX = 'sssc-subnet-'
_SECURITY_GROUP_NAME = 'sssc-sg'
_SERVER_NAME = 'sssc-server'
_KEY_NAME = 'sssc-root'
_KEY_PATH = f'./{_KEY_NAME}.pem'
_API_PORT = 29681
_AMIS = {
    'us-east-1': 'ami-09d3b3274b6c5d4aa',
    'us-east-2': 'ami-089a545a9ed9893b6',
    'us-west-1': 'ami-017c001a88dd93847',
    'us-west-2': 'ami-0d593311db5abb72b',
}

class EC2Cluster(Server):

    log = _ec2Logger()

    _init = False
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

    def __init__(self, status_file=None) -> None:
        """ 
        Attempts to load a StochSS-Compute cluster. Otherwise just initializes a new cluster.

        :param status_file: Optional. If provided, status updates will be written to a file with this path and name.
        :type str:

        """
        self.status_file = status_file
        self._client = boto3.client('ec2')
        self._resources = boto3.resource('ec2')
        region = get_session().get_config_variable('region')
        try:
            self._ami = _AMIS[region]
        except KeyError:
            self._set_status('region error')
            raise EC2Exception(f'Unsupported region. Currently Supported: {list(_AMIS.keys())}')

        try:
            self._load_cluster()      
        except ClientError as ce:
            self._set_status(ce.response['Error']['Code'])
            raise EC2Exception(ce.response['Error']['Message'])
        except ResourceException:
            self.clean_up()


    @property
    def address(self):
        """
        The server's IP address and port.
        """
        if self._server is None:
            raise EC2Exception('No server found. First launch a cluster.')
        if self._server.public_ip_address is None:
            self._server.reload()
        if self._server.public_ip_address is None:
            raise EC2Exception('No public address found.')

        return f'http://{self._server.public_ip_address}:{_API_PORT}'

    @property
    def status(self):
        if self._server is None:
            return self._status
        else:
            return self._server.state['Name']

    def _set_status(self, status):
        self._status = status
        if self.status_file is not None:
            with open(self.status_file, 'w') as file:
                file.write(status)

    def launch_single_node_instance(self, instanceType):
        """ 
        Launches a single node StochSS-Compute instance. Make sure to check instanceType pricing before launching. 

        :param instanceType: Example: 't3.nano' See full list here: https://aws.amazon.com/ec2/instance-types/ 
        :type instanceType: str
         """
        if self._init is True:
            raise EC2Exception('You cannot launch more than one StochSS-Compute cluster instance per account')
        
        self._set_status('launching')
        try:
            self._launch_network()
            self._create_root_key()
            self._launch_head_node(instanceType=instanceType)
        except ClientError as ce:
            self._set_status(ce.response['Error']['Code'])
            raise EC2Exception(ce.response['Error']['Message'])        
        self._set_status(self._server.state['Name'])

    def clean_up(self):
        """ 
        Deletes all cluster resources.
        """
        self._set_status('terminating')
        self._init = False

        vpc_search_filter = [
            {
                'Name': 'tag:Name',
                'Values': [
                    _VPC_NAME
                ]
            }
        ]
        try:
            vpc_response = self._client.describe_vpcs(Filters=vpc_search_filter)
            for vpc_dict in vpc_response['Vpcs']:
                vpc_id = vpc_dict['VpcId']
                vpc = self._resources.Vpc(vpc_id)
                for instance in vpc.instances.all():
                    instance.terminate()
                    self.log.info(f'Terminating "{instance.id}". This might take a minute.......')
                    instance.wait_until_terminated()
                    self._server = None
                    self.log.info(f'Instance {instance.id}" terminated.')
                for sg in vpc.security_groups.all():
                    if sg.group_name == _SECURITY_GROUP_NAME:
                        self.log.info(f'Deleting {sg.id}.......')
                        sg.delete()
                        self._server_security_group = None
                        self.log.info(f'Security group {sg.id} deleted.')
                    elif sg.group_name == 'default':
                        self._default_security_group = None
                for subnet in vpc.subnets.all():
                    self.log.info(f'Deleting {subnet.id}.......')
                    subnet.delete()
                    self._subnets['public'] = None
                    self.log.info(f'Subnet {subnet.id} deleted.')
                for igw in vpc.internet_gateways.all():
                    self.log.info(f'Detaching {igw.id}.......')
                    igw.detach_from_vpc(VpcId=vpc.vpc_id)
                    self.log.info(f'Gateway {igw.id} detached.')
                    self.log.info(f'Deleting {igw.id}.......')
                    igw.delete()
                    self.log.info(f'Gateway {igw.id} deleted.')
                self.log.info(f'Deleting {vpc.id}.......')
                vpc.delete()
                self._vpc = None
                self.log.info(f'VPC {vpc.id} deleted.')
            try:
                self._client.describe_key_pairs(KeyNames=[_KEY_NAME])
                key_pair = self._resources.KeyPair(_KEY_NAME)
                self.log.info(f'Deleting "{_KEY_NAME}".')
                key_pair.delete()
                self.log.info(f'Key Pair "{_KEY_NAME}" deleted.')
            except:
                # be more specific here
                pass
        except ClientError as ce:
            self._set_status(ce.response['Error']['Code'])
            raise EC2Exception(ce.response['Error']['Message'])
        self._delete_root_key()
        self._set_status('terminated')

    def _launch_network(self):
        """ 
        Launches required network resources.
        """
        self.log.info("Launching Network.......")
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
            self.log.info(f'Deleting "{_KEY_PATH}".')
            os.remove(_KEY_PATH)
            self.log.info(f'Root key deleted.')

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
sudo yum update -y
sudo yum -y install docker
sudo usermod -a -G docker ec2-user
sudo service docker start
sudo chmod 666 /var/run/docker.sock 
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
        self.log.info(f'Launching StochSS-Compute server instance. This might take a minute.......')
        try:
            response = self._client.run_instances(**kwargs)
        except ClientError as e:
            raise EC2Exception(e)
        instance_id = response['Instances'][0]['InstanceId']
        self._server = self._resources.Instance(instance_id)
        self._server.wait_until_exists()
        self._server.wait_until_running()

        self.log.info(f'Instance "{instance_id}" is running.')

        self._poll_launch_progress(['sssc'])

        self.log.info('Restricting server access to only your ip.')
        source_ip = self._get_source_ip(cloud_key)

        self._restrict_ingress(source_ip)
        self._init = True
        self.log.info('StochSS-Compute ready to go!')

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
                sleep(30)
                stdin,stdout,stderr = ssh.exec_command("docker container inspect -f '{{.State.Running}}' " + f'{container}')
                rc = stdout.channel.recv_exit_status()
                out = stdout.readlines()
                err = stderr.readlines()
                if rc == -1:
                    ssh.close()
                    raise EC2Exception("Something went wrong connecting to the server. No exit status provided by the server.")
                # Wait for yum update, docker install, container download
                if rc == 1 or rc == 127:
                    self.log.info('Waiting on Docker daemon.')
                    sshtries += 1
                    if sshtries >= 5:
                        ssh.close()
                        raise EC2Exception(f"Something went wrong with Docker. Max retry attempts exceeded.\nError:\n{''.join(err)}")
                if rc == 0:
                    if 'true\n' in out:
                        sleep(10)
                        self.log.info(f'Container "{container}" is running.')
                        break
        ssh.close()

    def _get_source_ip(self, cloud_key):
        """
        Ping the server to find the IP address associated with the request.

        :param cloud_key: A secret key which must match the random key used to launch the instance.
        :type cloud_key: str
        """
        source_ip_request = SourceIpRequest(cloud_key=cloud_key)
        response_raw = self._post(Endpoint.CLOUD, sub='/sourceip', request=source_ip_request)
        if not response_raw.ok:
            raise EC2Exception(response_raw.reason)
        response = SourceIpResponse._parse(response_raw.text)
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
                self._set_status('key error')
                
                raise ResourceException
            else:
                try:
                    keypair = self._client.describe_key_pairs(KeyNames=[_KEY_NAME]) 
                    if keypair is not None:
                        
                        self._set_status('key error')
                        raise ResourceException
                except:
                    pass
            return False
        if len(vpc_response['Vpcs']) == 2:
            self.log.warn(f'More than one VPC named "{_VPC_NAME}".')
            self._set_status('VPC error')
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
            self.log.warn(f'No instances named "{_SERVER_NAME}".')
            self._set_status('server error')
            errors = True
        for sg in vpc.security_groups.all():
            if sg.group_name == 'default':
                self._default_security_group = sg
            if sg.group_name == _SECURITY_GROUP_NAME:
                for rule in sg.ip_permissions:
                    if rule['FromPort'] == 29681 and rule['ToPort'] == 29681 and rule['IpRanges'][0]['CidrIp'] == '0.0.0.0/0':
                        self.log.warn(f'Security Group rule error.')
                        self._set_status('security group error')
                        errors = True
                self._server_security_group = sg
        if self._server_security_group is None:
            self.log.warn(f'No security group named "{_SECURITY_GROUP_NAME}".')
            self._set_status('security group error')
            errors = True
        for subnet in vpc.subnets.all():
            for tag in subnet.tags:
                if tag['Key'] == 'Name' and tag['Value'] == f'{_SUBNET_PREFIX}public':
                    self._subnets['public'] = subnet
                if tag['Key'] == 'Name' and tag['Value'] == f'{_SUBNET_PREFIX}private':
                    self._subnets['private'] = subnet
        if None in self._subnets.values():
            self.log.warn('Missing or misconfigured subnet.')
            self._set_status('subnet error')
            errors = True
        if errors is True:
            raise ResourceException
        else:
            self._init = True
            self.log.info('Cluster loaded.')
            self._set_status(self._server.state['Name'])
            return True

