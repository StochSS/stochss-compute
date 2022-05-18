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