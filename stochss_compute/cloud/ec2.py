from typing import List, Union
import boto3
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

        def authorize_SSH(self, groupName='sssc-sg', cidrIp='0.0.0.0/0'):
            sgargs = {
                'CidrIp': cidrIp,
                'FromPort': 22,
                'ToPort': 22,
                'IpProtocol': 'tcp',
            }
            resource = boto3.resource('ec2')
            sg = resource.SecurityGroup(self.security_group_id)
            # deal with return
            return sg.authorize_ingress(**sgargs)

        # TODO come back to this because it will be easier when we use our own custom security group & vpc (shouldn't be too hard)
        # note: might need different rules for dask, etc.

        # for now, only one rule per instance (I think that will still work) (downside is it only accepts port ranges)
        # def edit_ingress_rule(self, ipProtocol='tcp', fromPort=22, toPort=22, cidrIpv4='0.0.0.0/0', description='Inbound SSH'):
        #     client = boto3.client('ec2')
        #     resource = boto3.resource('ec2')
        #     sg = resource.SecurityGroup(self.security_group_id)
        #     sg_rule_id = client.describe_security_group_rules()['SecurityGroupRules'][0]['SecurityGroupRuleId']
        #     new_rule = [{
        #         'SecurityGroupRuleId': sg_rule_id,
        #         'SecurityGroupRule': {
        #             'IpProtocol': ipProtocol,
        #             'FromPort': fromPort,
        #             'ToPort': toPort,
        #             'CidrIpv4': cidrIpv4,
        #             'Description': description
        #         }
                
        #     }]
        #     return client.modify_security_group_rules(GroupId=self.security_group_id, SecurityGroupRules=new_rule)


    def __init__(self) -> None:
        self.client = boto3.client('ec2')
        self.resources = boto3.resource('ec2')
        self.returns = {}
        self.rootKey = self.SSHKey('sssc-root')
        self.instances = []
        

    def create_root_key(self, savePath='./', keyType='ed25519', keyFormat='pem') -> SSHKey:

        valid_formats = {'pem', 'ppk'}
        if keyFormat not in valid_formats:
            raise ValueError(f'keyFormat must be one of {valid_formats}.')

        valid_types = {'ed25519', 'rsa'}
        if keyType not in valid_types:
            raise ValueError(f'keyType must be one of {valid_types}.')

        key_path = f'{savePath}{self.rootKey.name}.{keyFormat}'

        try:
            key = open(key_path, 'x')
        except FileExistsError as e:
            print(f'StochSS-Compute root key detected in working directory. Using "{key_path}".')
            key_pair_response = self.client.describe_key_pairs(KeyNames=[self.rootKey.name])
            self.rootKey.id = key_pair_response['KeyPairs'][0]['KeyPairId']
            self.rootKey.fingerprint = key_pair_response['KeyPairs'][0]['KeyFingerprint']
            self.rootKey.path = key_path
            self.rootKey.type = key_pair_response['KeyPairs'][0]['KeyType']
            self.rootKey.format = keyFormat
            return self.rootKey

        response = self.client.create_key_pair(KeyName=self.rootKey.name, KeyType=keyType, KeyFormat=keyFormat)
        key.write(response['KeyMaterial'])
        key.close()
        os.chmod(key_path, 0o400)

        self.rootKey.id = response['KeyPairId']
        self.rootKey.fingerprint = response['KeyFingerprint']
        self.rootKey.path = key_path
        self.rootKey.type = keyType
        self.rootKey.format = keyFormat
        return self.rootKey

    # TODO
    def load_root_key():
        pass

    def delete_root_key(self) -> None:
        self.client.delete_key_pair(KeyName=self.rootKey.name)

    def launch_commands(self) -> str:
        # These aren't right, just a draft
        # The return gets passed to run_instances as 'UserData'
        # docker = {
        #     'docker0': '#!/bin/bash',
        #     'docker1': 'sudo yum install docker',
        #     'docker2': 'sudo amazon-linux-extras install docker',
        #     'docker3': 'sudo service docker start',
        #     'docker4': 'sudo usermod -a -G docker ec2-user',
        #     'docker5': 'docker run -it stochss/stochss-compute'
        # }
        docker = '''!/bin/bash
sudo yum install docker
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
docker run -it stochss/stochss-compute'''
        # dask = {
        #     'dask0': 'yum install distributed',
        #     'dask1': 'scheduler',
        #     'dask2': 'dask-worker ...'
        # }
        return '\n'.join(list(docker.values()))+'\n'
        # print('\n'.join(list(dask.values()))+'\n')

    def create_default_vpc(self):
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
            self.client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsSupport = { 'Value': True } )
            self.client.modify_vpc_attribute( VpcId = vpc_id , EnableDnsHostnames = { 'Value': True } )
            vpc = self.resources.Vpc(vpc_id)
            igw_response = self.client.create_internet_gateway()

        else:
            p.pprint(vpc_response)
            vpc_id = vpc_response['Vpcs'][0]['VpcId']
            
        return vpc_id

    def create_default_subnet(self, vpcId):
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
            self.client.modify_subnet_attribute(SubnetId = subnet_id, MapPublicIpOnLaunch = { 'Value': True })
        else:
            p.pprint(subnet_response)
            subnet_id = subnet_response['Subnets'][0]['SubnetId']
            
        return subnet_id

    def create_default_security_group(self, vpcId):
        # TODO
        vpc = self.resources.Vpc(vpcId)
        sg_response = vpc.create_security_group(Description='Default Security Group for StochSS-Compute.',GroupName='sssc-sg')
        return sg_response.group_id


    def launch_single_node_cluster(self):
        self.create_root_key()
        vpcId = self.create_default_vpc()
        print(f'vpcId: {vpcId}')
        subnetId = self.create_default_subnet(vpcId)
        print(f'subnetId: {subnetId}')
        sgId = self.create_default_security_group(vpcId)
        print(f'sgId: {sgId}')
        head = self.launch_instances(subnetId=subnetId, securityGroupId=sgId)
        print(f'head: {head}')
        head.authorize_SSH()

        return

    def launch_instances(self, *, subnetId, securityGroupId, name='stochss-compute', imageId='ami-0fa49cc9dc8d62c84', instanceType='t3.micro', minCount=1, maxCount=1) -> Union[List[Instance], Instance]:
        valid_types = {'stochss-compute', 'scheduler', 'worker'}
        if name not in valid_types:
            raise ValueError(f'"name" must be one of {valid_types}.')
        docker = '''!/bin/bash
echo "SUP"'''
#         docker = '''!/bin/bash
# sudo yum install docker
# sudo amazon-linux-extras install docker
# sudo service docker start
# sudo usermod -a -G docker ec2-user
# docker run -it stochss/stochss-compute'''
        kwargs = {
            'ImageId': imageId, 
            'InstanceType': instanceType,
            'KeyName': self.rootKey.name,
            'MinCount': minCount, 
            'MaxCount': maxCount,
            # 'SubnetId': subnetId,
            # 'SecurityGroupIds': [securityGroupId],
            # 'UserData': docker,
            # 'NetworkInterfaces':[
            #     {
            #         'DeviceIndex': 0,
            #         'SubnetId' : subnetId,
            #         'Groups': [
            #             securityGroupId
            #         ],
            #         'AssociatePublicIpAddress': True            
            #     }]
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
            # keep it simple, only allow one security group (not sure how it would work with multiple, seems unnecessary for this application)
            # however, in case the user already uses the default security group and vpc for other things, will need to create one specifically for sssc
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

    def terminate_all_instances(self) -> None:
        describe_instances = self.client.describe_instances()
        instance_ids = []
        for reservation in describe_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        print(instance_ids)
        self.client.terminate_instances(InstanceIds=instance_ids)

    def delete_vpc(self):
        # will need to wait on instance termination
        pass

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

    # def get_public_DNS(self, instance_id) -> str:
    #     self.resources = boto3.resource('ec2')
    #     instance = self.resources.Instance(instance_id)
    #     return instance.public_dns_name

        