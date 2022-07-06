from stochss_compute import RemoteSimulation, ComputeServer
from stochss_compute.compute_server import Endpoint
from .api import SourceIpRequest, SourceIpResponse
from ..remote_utils import unwrap_or_err

from gillespy2 import Model

import boto3
from botocore.exceptions import ClientError

import os
from time import sleep
from secrets import token_hex


class Cluster():

    _client = boto3.client('ec2')
    _resources = boto3.resource('ec2')
    _restricted: bool = False
    _cloud_key: str = ''
    _subnet = None
    _security_group = None
    _vpc = None
    _server = None
    _scheduler = None
    _workers = []
    _root_key = None
    _key_path = ''

    def __init__(self) -> None:
        # TODO this will have to go after the address is made in launch
        pass
        # see if _restricted
        # re-load cluster by setting _resources
        

    def _create_root_key(self):
        name = 'stochss-root'
        savePath='./'
        keyType='ed25519'
        keyFormat='pem'

        self._key_path = f'{savePath}{name}.{keyFormat}'

        if os.path.exists(self._key_path):
            print(f'StochSS-Compute root key detected in working directory. Using "{self._key_path}".')
            try:
                key_pair_response = self._client.describe_key_pairs(KeyNames=[name])
            except ClientError as error:
                if error.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
                    print(error.response['Error']['Message'])
                    print(f'An outdated key detected in working directory:  "{name}".')
                    print(f'Call clean_up() and re-try the operation.')
                    raise error
            self._root_key = self._resources.KeyPair(name)
            return self._root_key

        
        try:
            response = self._client.create_key_pair(KeyName=name, KeyType=keyType, KeyFormat=keyFormat)
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                print(error.response['Error']['Message'])
                print(f'If you still have your key, move it into this working directory and make sure that it is named "{name}".')
                print(f'Otherwise, call clean_up() and re-try the operation.')
                raise error
        key = open(self._key_path, 'x')
        key.write(response['KeyMaterial'])
        key.close()
        os.chmod(self._key_path, 0o400)

        self._root_key = self._resources.KeyPair(name)
        return self._root_key


    def _delete_root_key(self) -> None:
        name = 'stochss-root'
        self._client.delete_key_pair(KeyName=name)
        if os.path.exists(self._key_path):
            os.remove(self._key_path)
        self._root_key = None
        self._key_path = ''

    def _create_sssc_vpc(self):
        vpc_cidrBlock = '172.31.0.0/16'
        vpc_search_filter = [
            {
                'Name': 'tag:Name',
                'Values': [
                    'sssc-vpc'
                ]
            },
            {
                'Name': 'cidr',
                'Values': [
                    vpc_cidrBlock
                ]
            }
        ]

        vpc_response = self._client.describe_vpcs(Filters=vpc_search_filter)
        
        if len(vpc_response['Vpcs']) == 0:
            vpc_tag = [
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'sssc-vpc'
                        }
                    ]
                }
            ]
            vpc_response = self._client.create_vpc(CidrBlock=vpc_cidrBlock, TagSpecifications=vpc_tag)
            vpc_id = vpc_response['Vpc']['VpcId']
            self._client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsSupport={'Value': True})
            self._client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsHostnames={'Value': True })
            igw_response = self._client.create_internet_gateway()
            igw_id = igw_response['InternetGateway']['InternetGatewayId']
            self._vpc = self._resources.Vpc(vpc_id)
            self._vpc.attach_internet_gateway(InternetGatewayId=igw_id)
            for rtb in self._vpc.route_tables.all():
                if rtb.associations_attribute[0]['Main'] == True:
                    rtb_id = rtb.route_table_id
            self._client.create_route(RouteTableId=rtb_id, GatewayId=igw_id, DestinationCidrBlock='0.0.0.0/0')

        else:
            vpc_id = vpc_response['Vpcs'][0]['VpcId']
            self._vpc = self._resources.Vpc(vpc_id)
        
        return self._vpc

    def _create_sssc_subnet(self):
        subnet_cidrBlock = '172.31.0.0/20'
        subnet_search_filter = [
            {
                'Name': 'vpc-id',
                'Values': [
                    self._vpc.id
                ]
            },
            {
                'Name': 'tag:Name',
                'Values': [
                    'sssc-subnet-0'
                ]
            },
            {
                'Name': 'cidr',
                'Values': [
                    subnet_cidrBlock
                ]
            }
        ]
        subnet_response = self._client.describe_subnets(Filters=subnet_search_filter)

        if len(subnet_response['Subnets']) == 0:
            subnet_tag = [
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'sssc-subnet-0'
                        }
                    ]
                }
            ]
            self._subnet = self._vpc.create_subnet(CidrBlock=subnet_cidrBlock, TagSpecifications=subnet_tag)
            self._client.modify_subnet_attribute(SubnetId=self._subnet.id, MapPublicIpOnLaunch={'Value': True})
        else:
            subnet_id = subnet_response['Subnets'][0]['SubnetId']
            self._subnet = self._resources.Subnet(subnet_id)
            
        return self._subnet

    def _create_sssc_security_group(self):
        self._security_group = self._vpc.create_security_group(Description='Default Security Group for StochSS-Compute.', GroupName='sssc-sg')
        sshargs = {
            'CidrIp': '0.0.0.0/0',
            'FromPort': 22,
            'ToPort': 22,
            'IpProtocol': 'tcp',
        }
        self._security_group.authorize_ingress(**sshargs)
        sgargs = {
            'CidrIp': '0.0.0.0/0',
            'FromPort': 29681,
            'ToPort': 29681,
            'IpProtocol': 'tcp',
            'TagSpecifications': [
                {
                    'ResourceType': 'security-group-rule',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': '29681'
                        },
                    ]
                },
            ]
        }
        self._security_group.authorize_ingress(**sgargs)
        return self._security_group

    def _restrict_ingress(self, ipAddress: str = ''):
        filter=[
            {
                'Name': 'group-name',
                'Values': [
                    'sssc-sg',
                ]
            },
        ]
        sg_response = self._client.describe_security_groups(Filters=filter)
        sg_id = sg_response['SecurityGroups'][0]['GroupId']
        filter2=[
            {
                'Name': 'group-id',
                'Values': [
                    sg_id,
                ]
            },
            {
                'Name': 'tag:Name',
                'Values': [
                    '29681',
                ]
            },
        ]
        sgr_response = self._client.describe_security_group_rules(Filters=filter2)
        sgr_id = sgr_response['SecurityGroupRules'][0]['SecurityGroupRuleId']
        securityGroupRules=[
            {
                'SecurityGroupRuleId': sgr_id,
                'SecurityGroupRule': {
                    'IpProtocol': 'tcp',
                    'FromPort': 29681,
                    'ToPort': 29681,
                    'CidrIpv4': f'{ipAddress}/32',
                    'Description': 'Restricts cluster access.'
                }
            },
        ]
        self._client.modify_security_group_rules(GroupId=sg_id, SecurityGroupRules=securityGroupRules)
        sgr_response = self._client.describe_security_group_rules(Filters=filter2)

    def _launch_network(self):
        self._create_sssc_vpc()
        self._create_sssc_subnet()
        self._create_sssc_security_group()
        return self._vpc


    def _launch_server(self, *, imageId='ami-0fa49cc9dc8d62c84', instanceType='t3.micro'):
        name = 'sssc-server'
        cloud_key = token_hex(32)

        launch_commands = f'''#!/bin/bash
sudo yum update -y
sudo yum -y install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chmod 666 /var/run/docker.sock 
docker run --network host --rm -e CLOUD_LOCK={cloud_key} --name sssc stochss/stochss-compute:dev > /home/ec2-user/sssc-out 2> /home/ec2-user/sssc-err
'''
        kwargs = {
            'ImageId': imageId, 
            'InstanceType': instanceType,
            'KeyName': self._root_key.key_name,
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
                            'Value': name
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
        self._cloud_key = cloud_key

        print(f'Instance "{instance_id}" is running.')
        print(f'Downloading updates and starting server......')
        return self._server

    def _poll_launch_progress():
        pass

    def launch_single_node_cluster(self):
        self._launch_network()
        self._create_root_key()
        return self._launch_server()
        
    def clean_up(self):
        vpc_cidrBlock = '172.31.0.0/16'
        vpc_search_filter = [
            {
                'Name': 'tag:Name',
                'Values': [
                    'sssc-vpc'
                ]
            },
            {
                'Name': 'cidr',
                'Values': [
                    vpc_cidrBlock
                ]
            }
        ]
        # instead, can just check to see if reference is None?
        vpc_response = self._client.describe_vpcs(Filters=vpc_search_filter)
        if len(vpc_response['Vpcs']) != 0:
            vpc = self._vpc
            for instance in vpc.instances.all():
                instance.terminate()
                print(f'Terminating "{instance.id}". This might take a minute.......')
                instance.wait_until_terminated()
                self._server = None
                self._scheduler = None
                self._workers = []
                print(f'Instance {instance.id}" terminated.')
            # TODO seems to still be launching into default security group? I think this is the defined behavior
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
        
        print(f'Deleting {self._root_key.key_pair_id}.......')
        self._delete_root_key()

        print(f'Root key deleted.')


    def reload_cluster():
        # Will reload the cluster in case the user messes something up in the dashboard/something goes wrong.
        # basically will just be checking aws to see if the properly named resources exist in order to load up everything into the object references
        pass

    def _get_source_ip(self):
        ip = self._server.public_ip_address
        server = ComputeServer(ip, port=29681)
        source_ip_request = SourceIpRequest(cloud_key=self._cloud_key)
        source_ip_response = unwrap_or_err(SourceIpResponse, server.post(Endpoint.CLOUD, sub='/sourceip', request=source_ip_request))
        return source_ip_response.source_ip

    def run(self, model: Model):
        ip = self._server.public_ip_address
        server = ComputeServer(ip, port=29681)
        if self._restricted == False:
            source_ip = self._get_source_ip()
            self._restrict_ingress(source_ip)
            self._restricted = True
        return RemoteSimulation.on(server).with_model(model).run()


        