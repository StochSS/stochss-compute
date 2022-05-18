import boto3
import os

client = boto3.client('ec2')
returns = {}
keyName = 'stochss-compute-root'

def create_key_pair():
    returns['key'] = client.create_key_pair(KeyName=keyName, KeyType='ed25519',KeyFormat='pem')
    key = open('key.pem', 'w')
    key.write(returns['key']['KeyMaterial'])
    key.close()
    os.chmod('key.pem', 400)

def delete_key_pair():
    client.delete_key_pair(KeyName=keyName)

def launch_instance():
    ami = 'ami-0fa49cc9dc8d62c84'
    returns['launch'] = client.run_instances(ImageId=ami, InstanceType='t3.micro', MinCount=1, MaxCount=1)
    print(returns['launch'])

def terminate_instance():
    describe_instances = client.describe_instances()
    instance_ids = []
    for reservation in describe_instances['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
    print(instance_ids)
    client.terminate_instances(InstanceIds=instance_ids)