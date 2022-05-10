import json
import boto3
from botocore.config import Config
from time import sleep

create_cluster_args = {'name':'stochss-compute-dask' }

def create_vpc():
    CFclient = boto3.client("cloudformation")
    vpc_return = CFclient.create_stack(TemplateURL="https://s3.us-west-2.amazonaws.com/amazon-eks/cloudformation/2020-10-29/amazon-eks-vpc-private-subnets.yaml", StackName="stochss-compute-vpc")
    stack_id = vpc_return['StackId']
    vpc_resources = CFclient.describe_stack_resources(StackName=stack_id)
    cloudformation = boto3.resource('cloudformation')
    vpc_stack = cloudformation.Stack('stochss-compute-vpc')
    while vpc_stack.stack_status != 'CREATE_COMPLETE':
        sleep(10)
        vpc_stack = cloudformation.Stack('stochss-compute-vpc')
    print(vpc_stack.__dict__)

def create_role():
    cluster_role_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "eks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    IAMclient = boto3.client("iam")
    IAM_cr_return = IAMclient.create_role(RoleName='eksClusterRole', AssumeRolePolicyDocument=json.dumps(cluster_role_trust_policy))
    print(IAM_cr_return)
    create_cluster_args['roleArn'] = IAM_cr_return['Role']['Arn']
    print()
    try:
        IAM_ar_return =  IAMclient.attach_role_policy(
            RoleName='eksClusterRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
    except Exception as error :
        print(error)

    print(IAM_ar_return)

def create_cluster():
    pass

def clean_up():
    CFclient = boto3.client("cloudformation")
    CFclient.delete_stack(StackName="stochss-compute-vpc")
    iam = boto3.resource('iam')
    eksClusterRole = iam.Role("eksClusterRole")
    eksClusterRole.detach_policy(
        PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
    eksClusterRole.delete()