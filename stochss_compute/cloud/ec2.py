from typing import List, Union
import boto3
from botocore.exceptions import ClientError
import os
import pprint

p = pprint.PrettyPrinter(indent=1)

class EC2Cluster:

    class SSHKey:
        def __init__(self, name) -> None:
            self.name = name
            
    class Instance:
        # TODO
        # find out best way to make boto3 objects 'private' (do not need to be accessible) PY OH PY
        # find out where & how to associate this class within library
        def __init__(self, id) -> None:
            resource = boto3.resource('ec2')
            self._remote = resource.Instance(id)

        def state(self) -> str:
            self._remote.load()
            return self._remote.state
        
        def reboot(self) -> None:
            self._remote.reboot()

        def start(self) -> None:
            self._remote.start()
            self._remote.wait_until_running()
        
        def stop(self) -> None:
            self._remote.stop()
            self._remote.wait_until_stopped()

        def terminate(self) -> None:
            self._remote.terminate()
            self._remote.wait_until_terminated()

    def __init__(self) -> None:
        self.client = boto3.client('ec2')
        self.resources = boto3.resource('ec2')
        self.returns = {}
        self.rootKey = self.SSHKey('sssc-root')
        self.instances = []
        

    def _create_root_key(self) -> SSHKey:
        savePath='./'
        keyType='ed25519'
        keyFormat='pem'
        valid_formats = {'pem', 'ppk'}
        if keyFormat not in valid_formats:
            raise ValueError(f'keyFormat must be one of {valid_formats}.')

        valid_types = {'ed25519', 'rsa'}
        if keyType not in valid_types:
            raise ValueError(f'keyType must be one of {valid_types}.')

        key_path = f'{savePath}{self.rootKey.name}.{keyFormat}'

        if os.path.exists(key_path):
            print(f'StochSS-Compute root key detected in working directory. Using "{key_path}".')
            try:
                key_pair_response = self.client.describe_key_pairs(KeyNames=[self.rootKey.name])
            except ClientError as error:
                if error.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
                    print(error.response['Error']['Message'])
                    print(f'An outdated key detected in working directory:  "{self.rootKey.name}".')
                    print(f'Call clean_up() and re-try the operation.')
                    raise error
            self.rootKey.id = key_pair_response['KeyPairs'][0]['KeyPairId']
            self.rootKey.fingerprint = key_pair_response['KeyPairs'][0]['KeyFingerprint']
            self.rootKey.path = key_path
            self.rootKey.type = key_pair_response['KeyPairs'][0]['KeyType']
            self.rootKey.format = keyFormat
            return self.rootKey

        
        try:
            response = self.client.create_key_pair(KeyName=self.rootKey.name, KeyType=keyType, KeyFormat=keyFormat)
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                print(error.response['Error']['Message'])
                print(f'If you still have your key, move it into this working directory and make sure that it is named "{self.rootKey.name}".')
                print(f'Otherwise, call clean_up() and re-try the operation.')
                raise error
        key = open(key_path, 'x')
        key.write(response['KeyMaterial'])
        key.close()
        os.chmod(key_path, 0o400)

        self.rootKey.id = response['KeyPairId']
        self.rootKey.fingerprint = response['KeyFingerprint']
        self.rootKey.path = key_path
        self.rootKey.type = keyType
        self.rootKey.format = keyFormat
        return self.rootKey


    def _delete_root_key(self) -> None:
        self.client.delete_key_pair(KeyName=self.rootKey.name)
        os.remove(f'{self.rootKey.name}.pem')

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
            p.pprint(vpc_response)
            vpc_id = vpc_response['Vpcs'][0]['VpcId']
            
        return vpc_id

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
            p.pprint(subnet_response)
            subnet_id = subnet_response['Subnets'][0]['SubnetId']
            
        return subnet_id

    def _create_sssc_security_group(self, vpcId):
        vpc = self.resources.Vpc(vpcId)
        sg = vpc.create_security_group(Description='Default Security Group for StochSS-Compute.', GroupName='sssc-sg')
        sgargs = {
            'CidrIp': '0.0.0.0/0',
            'FromPort': 22,
            'ToPort': 22,
            'IpProtocol': 'tcp',
        }
        sg.authorize_ingress(**sgargs)
        return sg.group_id

    def _launch_network(self):
        vpcId = self._create_sssc_vpc()
        subnetId = self._create_sssc_subnet(vpcId)
        sgId = self._create_sssc_security_group(vpcId)
        return (subnetId, sgId)

    def launch_single_node_cluster(self):
        (subnetId, sgId) = self._launch_network()
        self._create_root_key()
        return self._launch_instances(subnetId=subnetId, securityGroupId=sgId)

    def _launch_instances(self, *, subnetId, securityGroupId, name='stochss-compute', imageId='ami-0fa49cc9dc8d62c84', instanceType='t3.micro', minCount=1, maxCount=1) -> Union[List[Instance], Instance]:
        valid_types = {'stochss-compute', 'scheduler', 'worker'}
        if name not in valid_types:
            raise ValueError(f'"name" must be one of {valid_types}.')
        launch_commands = '''!/bin/bash
sudo yum update -y
sudo yum -y install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chmod 666 /var/run/docker.sock
docker run -it --network host stochss/stochss-compute:dev'''
        kwargs = {
            'ImageId': imageId, 
            'InstanceType': instanceType,
            'KeyName': self.rootKey.name,
            'MinCount': minCount, 
            'MaxCount': maxCount,
            'SubnetId': subnetId,
            'SecurityGroupIds': [securityGroupId],
            'UserData': launch_commands,
            }

        response = self.client.run_instances(**kwargs)
        self.returns['launch'] = response # just for debug or keep? (if keeping make a list)
        instance_ids = []
        for instance in response['Instances']:
            instance_ids.append(instance['InstanceId'])
        instances = []
        for i, id in enumerate(instance_ids):
            instance = self.resources.Instance(id)
            instance.wait_until_running()
            print(f'Instance "{id}" is now ready.')
            _instance = self.Instance(id) #consider changing name due to similarity with boto3 class name
            if name =='worker':
                _instance.name = f'sssc-{name}-{i}'
            elif name == 'scheduler':
                _instance.name = f'sssc-{name}'
            else:
                _instance.name = name

            # TODO find out how to best refactor this (probably just the obvious)
            _instance.architechture = instance.architecture
            _instance.cores = instance.cpu_options['CoreCount']
            _instance.threads_per_core = instance.cpu_options['ThreadsPerCore']
            _instance.image_id = instance.image_id
            _instance.instance_type = instance.instance_type
            _instance.key_name = instance.key_name
            _instance.launch_time = instance.launch_time
            _instance.availability_zone = instance.placement['AvailabilityZone']
            _instance.platform = instance.platform_details
            _instance.private_dns_name = instance.private_dns_name
            _instance.private_ip_address = instance.private_ip_address
            _instance.public_dns_name = instance.public_dns_name
            _instance.public_ip_address = instance.public_ip_address
            _instance.root_device_name = instance.root_device_name
            _instance.root_device_type = instance.root_device_type
            _instance.security_group_name = instance.security_groups[0]['GroupName']
            _instance.security_group_id = instance.security_groups[0]['GroupId']
            _instance.subnet_id = instance.subnet_id
            # virtualization type?
            _instance.vpc_id = instance.vpc_id

            instances.append(_instance)
        self.instances.extend(instances)

        if len(instances) == 1:
            return instances[0]
        if len(instances) > 1:
            return instances

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
        instance_ids = []
        for reservation in running_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        return instance_ids


        