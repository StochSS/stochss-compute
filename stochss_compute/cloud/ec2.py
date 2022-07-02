from typing import List, Union
import boto3
from botocore.exceptions import ClientError
import os
from gillespy2 import Model
from stochss_compute import RemoteSimulation, ComputeServer
from secrets import token_bytes

class Cluster():

    client = boto3.client('ec2')
    resources = boto3.resource('ec2')
    unlocked: bool = False
    cloud_key: str = ''
    subnet = None
    security_group = None
    vpc = None
    server = None
    scheduler = None
    workers = []
    root_key = None
    key_path = ''

    def __init__(self) -> None:
        self.returns = {}
        # see if unlocked
        

    def _create_root_key(self):
        name = 'stochss-root'
        savePath='./'
        keyType='ed25519'
        keyFormat='pem'

        self.key_path = f'{savePath}{name}.{keyFormat}'

        if os.path.exists(self.key_path):
            print(f'StochSS-Compute root key detected in working directory. Using "{self.key_path}".')
            try:
                key_pair_response = self.client.describe_key_pairs(KeyNames=[name])
            except ClientError as error:
                if error.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
                    print(error.response['Error']['Message'])
                    print(f'An outdated key detected in working directory:  "{name}".')
                    print(f'Call clean_up() and re-try the operation.')
                    raise error
            self.root_key = self.resources.KeyPair(name)
            return self.root_key

        
        try:
            response = self.client.create_key_pair(KeyName=name, KeyType=keyType, KeyFormat=keyFormat)
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                print(error.response['Error']['Message'])
                print(f'If you still have your key, move it into this working directory and make sure that it is named "{name}".')
                print(f'Otherwise, call clean_up() and re-try the operation.')
                raise error
        key = open(self.key_path, 'x')
        key.write(response['KeyMaterial'])
        key.close()
        os.chmod(self.key_path, 0o400)

        self.root_key = self.resources.KeyPair(name)
        return self.root_key


    def _delete_root_key(self) -> None:
        name = 'stochss-root'
        self.client.delete_key_pair(KeyName=name)
        if os.path.exists(self.key_path):
            os.remove(self.key_path)

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

        vpc_response = self.client.describe_vpcs(Filters=vpc_search_filter)
        
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
            vpc_response = self.client.create_vpc(CidrBlock=vpc_cidrBlock, TagSpecifications=vpc_tag)
            vpc_id = vpc_response['Vpc']['VpcId']
            self.client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsSupport={'Value': True})
            self.client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsHostnames={'Value': True })
            igw_response = self.client.create_internet_gateway()
            igw_id = igw_response['InternetGateway']['InternetGatewayId']
            vpc = self.resources.Vpc(vpc_id)
            vpc.attach_internet_gateway(InternetGatewayId=igw_id)
            for rtb in vpc.route_tables.all():
                if rtb.associations_attribute[0]['Main'] == True:
                    rtb_id = rtb.route_table_id
            self.client.create_route(RouteTableId=rtb_id, GatewayId=igw_id, DestinationCidrBlock='0.0.0.0/0')

        else:
            vpc_id = vpc_response['Vpcs'][0]['VpcId']
        
        self.vpc = self.resources.Vpc(vpc_id)
        return self.vpc

    def _create_sssc_subnet(self, vpcId):
        subnet_cidrBlock = '172.31.0.0/20'
        subnet_search_filter = [
            {
                'Name': 'vpc-id',
                'Values': [
                    vpcId
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
        subnet_response = self.client.describe_subnets(Filters=subnet_search_filter)
        if len(subnet_response['Subnets']) == 0:
            vpc = self.resources.Vpc(vpcId)
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
            subnet_response = vpc.create_subnet(CidrBlock=subnet_cidrBlock, TagSpecifications=subnet_tag)
            subnet_id = subnet_response.subnet_id
            self.client.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={'Value': True})
        else:
            subnet_id = subnet_response['Subnets'][0]['SubnetId']
        self.subnet = self.resources.Subnet(subnet_id)
            
        return self.subnet

    def _create_sssc_security_group(self, vpcId):
        vpc = self.resources.Vpc(vpcId)
        sg = vpc.create_security_group(Description='Default Security Group for StochSS-Compute.', GroupName='sssc-sg')
        sshargs = {
            'CidrIp': '0.0.0.0/0',
            'FromPort': 22,
            'ToPort': 22,
            'IpProtocol': 'tcp',
        }
        sg.authorize_ingress(**sshargs)
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
        sg.authorize_ingress(**sgargs)
        # test this by seeing if permissions change or not
        # sg.reload()
        self.security_group = sg
        return self.security_group

    def _restrict_ingress(self, ipAddress: str = ''):
        filter=[
            {
                'Name': 'group-name',
                'Values': [
                    'sssc-sg',
                ]
            },
        ]
        sg_response = self.client.describe_security_groups(Filters=filter)
        # print(sg_response)
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
        sgr_response = self.client.describe_security_group_rules(Filters=filter2)
        print(sgr_response)
        sgr_id = sgr_response['SecurityGroupRules'][0]['SecurityGroupRuleId']
        securityGroupRules=[
            {
                'SecurityGroupRuleId': sgr_id,
                'SecurityGroupRule': {
                    'IpProtocol': 'tcp',
                    'FromPort': 29681,
                    'ToPort': 29681,
                    # 'CidrIpv4': f'{ipAddress}/32',
                    'CidrIpv4': '0.0.0.0/0',
                    'Description': 'TEST'
                }
            },
        ]
        self.client.modify_security_group_rules(GroupId=sg_id, SecurityGroupRules=securityGroupRules)
        sgr_response = self.client.describe_security_group_rules(Filters=filter2)
        print(sgr_response)

    def _launch_network(self):
        self._create_sssc_vpc()
        self._create_sssc_subnet(self.vpc.id)
        self._create_sssc_security_group(self.vpc.id)

    def launch_single_node_cluster(self):
        self._launch_network()
        self._create_root_key()
        return self._launch_instances(subnetId=self.subnet.id, securityGroupId=self.security_group.id)

    def _launch_server(self, *, subnetId, securityGroupId, imageId='ami-0fa49cc9dc8d62c84', instanceType='t3.micro',):
        token = token_bytes(8)
        launch_commands = f'''!/bin/bash
sudo yum update -y
sudo yum -y install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chmod 666 /var/run/docker.sock
docker run -it --network host -e CLOUD_KEY={token} stochss/stochss-compute:dev'''
        kwargs = {
            'ImageId': imageId, 
            'InstanceType': instanceType,
            'KeyName': self.rootKey.key_name,
            'MinCount': 1, 
            'MaxCount': 1,
            'SubnetId': subnetId,
            'SecurityGroupIds': [securityGroupId],
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': f'sssc-server'
                        },
                    ]
                },
            ],
            # 'UserData': launch_commands,
            }
        print(f'Launching StochSS-Compute server instance.......(This could take a minute)')
        response = self.client.run_instances(**kwargs)
        self.returns['launch'] = response # just for debug or keep?
        instance_id = response['Instances'][0]['InstanceId']
        self.server = self.resources.Instance(id)
        self.server.wait_until_running()
        print(f'Instance "{instance_id}" is now ready.')
        return self.server

    def _terminate_all_instances(self) -> None:
        describe_instances = self.client.describe_instances()
        instance_ids = []
        for reservation in describe_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        print(instance_ids)
        self.client.terminate_instances(InstanceIds=instance_ids)

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

        vpc_response = self.client.describe_vpcs(Filters=vpc_search_filter)
        if len(vpc_response['Vpcs']) != 0:
            vpc_id = vpc_response['Vpcs'][0]['VpcId']
            vpc = self.resources.Vpc(vpc_id)
            for instance in vpc.instances.all():
                instance.terminate()
                print(f'Terminating "{instance.id}". This might take a minute.......')
                instance.wait_until_terminated()
                print(f'Instance {instance.id}" terminated.')
            # TODO seems to still be launching into default security group?
            for sg in vpc.security_groups.all():
                if sg.group_name == 'sssc-sg':
                    print(f'Deleting {sg.id}.......')
                    sg.delete()
                    print(f'Security group {sg.id} deleted.')
            for subnet in vpc.subnets.all():
                print(f'Deleting {subnet.id}.......')
                subnet.delete()
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
            print(f'VPC {vpc.id} deleted.')
        self._delete_root_key()

    def _get_running(self) -> List[str]:
        kwargs = {
            'Filters':[
                {
                    'Name':'instance-state-name',
                    'Values':[
                        'running'
                    ]
                }
            ]
        }
        client = boto3.client('ec2')
        running_instances = client.describe_instances(**kwargs)
        # make a dictionary from describe instances
        instance_ids = []
        for reservation in running_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        return instance_ids


    def run(self, model: Model):
        myServer = ComputeServer("localhost", port=29681)
        if self.unlocked == False:
            unlock_response = RemoteSimulation.on(myServer).with_model(model).run(unlock=True)

        