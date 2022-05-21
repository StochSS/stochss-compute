from typing import List
import boto3
import os
from time import sleep
import pprint

p = pprint.PrettyPrinter(indent=1)

class SSSCAWS:

    def __init__(self) -> None:
        self.client = boto3.client('ec2')
        self.resources = boto3.resource('ec2')
        self.returns = {}
        self.keyName = 'stochss-compute-root'
        

    def create_key_pair(self, path='./') -> str:
        self.returns['key'] = self.client.create_key_pair(KeyName=self.keyName, KeyType='ed25519',KeyFormat='pem')
        key = open(f'{path}{self.keyName}.pem', 'w')
        key.write(self.returns['key']['KeyMaterial'])
        key.close()
        os.chmod(f'{path}{self.keyName}.pem', 400)
        return f'{path}{self.keyName}.pem'

    def delete_key_pair(self) -> None:
        keyName = 'stochss-compute-root'
        self.client.delete_key_pair(KeyName=keyName)
    """
    [EC2-VPC] If you don't specify a subnet ID, we choose a default subnet from your default VPC for you.
    If you don't have a default VPC, you must specify a subnet ID in the request.

    [EC2-Classic] If don't specify an Availability Zone, we choose one for you.
    Some instance types must be launched into a VPC. If you do not have a default VPC, or if you do not specify a subnet ID, 
    the request fails. For more information, see Instance types available only in a VPC .

    [EC2-VPC] All instances have a network interface with a primary private IPv4 address.
    If you don't specify this address, we choose one from the IPv4 range of your subnet.
    Not all instance types support IPv6 addresses. For more information, see Instance types .

    If you don't specify a security group ID, we use the default security group. For more information, see Security groups .

    If any of the AMIs have a product code attached for which the user has not subscribed, the request fails.
    """

    def launch_instances(self) -> List[str]:
        ami = 'ami-0fa49cc9dc8d62c84'
        kwargs = {
            'ImageId':ami, 
            'InstanceType':'t3.micro',
            'KeyName': self.keyName,
            'MinCount':1, 
            'MaxCount':1
            }
        response = self.client.run_instances(**kwargs)
        self.returns['launch'] = response
        p.pprint(response)
        self.security_group = response['Instances'][0]['SecurityGroups'][0]['GroupId']
        instance_ids = []
        for instance in response['Instances']:
            instance_ids.append(instance['InstanceId'])
        p.pprint(instance_ids)
        for id in instance_ids:
            state = self.resources.Instance(id).state['Name']
            while state != 'running':
                print(f'Instance {id} is {state}.')
                sleep(10)
                state = self.resources.Instance(id).state['Name']
            print(f'Instance {id} is {state}.')
        return instance_ids

    def terminate_instances(self) -> None:
        describe_instances = self.client.describe_instances()
        instance_ids = []
        for reservation in describe_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        print(instance_ids)
        self.client.terminate_instances(InstanceIds=instance_ids)

    def get_running_instances() -> List[str]:
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

    def get_public_DNS(self, instance_id) -> str:
        self.resources = boto3.resource('ec2')
        instance = self.resources.Instance(instance_id)
        return instance.public_dns_name

        