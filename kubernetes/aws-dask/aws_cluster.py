import json
import boto3
import botocore.exceptions
from time import sleep

create_cluster_args = { 'name':'stochss-compute-dask' }
create_nodegroup_args = { 'clusterName':'stochss-compute-dask', 'nodegroupName': 'dask-0', 'scalingConfig': {'minSize': 2, 'maxSize': 5, 'desiredSize': 3}, 'instanceTypes': ['t3.micro'] }         

def create_vpc():
    CFclient = boto3.client('cloudformation')
    vpc_response = CFclient.create_stack(TemplateURL='https://s3.us-west-2.amazonaws.com/amazon-eks/cloudformation/2020-10-29/amazon-eks-vpc-private-subnets.yaml', StackName='stochss-compute-vpc')
    # stack_id = vpc_response['StackId']
    # vpc_resources = CFclient.describe_stack_resources(StackName=stack_id)
    cloudformation = boto3.resource('cloudformation')
    vpc_stack = cloudformation.Stack('stochss-compute-vpc')
    while vpc_stack.stack_status != 'CREATE_COMPLETE':
        sleep(10)
        vpc_stack = cloudformation.Stack('stochss-compute-vpc')
    vpc_id = vpc_stack.Resource('VPC').physical_resource_id
    sg_id = vpc_stack.Resource('ControlPlaneSecurityGroup').physical_resource_id
    print(vpc_id)
    ec2 = boto3.resource('ec2')
    subnet_ids = [subnet.id for subnet in ec2.Vpc(vpc_id).subnets.all()]
    create_cluster_args['resourcesVpcConfig'] = {'subnetIds':subnet_ids,'securityGroupIds':[sg_id]}
    create_nodegroup_args['subnets'] = subnet_ids
    print(create_cluster_args)


def create_cluster_role():
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
    IAM_cr_response = IAMclient.create_role(RoleName='eksClusterRole', AssumeRolePolicyDocument=json.dumps(cluster_role_trust_policy))
    print(IAM_cr_response)
    create_cluster_args['roleArn'] = IAM_cr_response['Role']['Arn']
    try:
        IAM_ar_response =  IAMclient.attach_role_policy(
            RoleName='eksClusterRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
    except Exception as error :
        print(error)

    print(IAM_ar_response)


def create_node_role():
    node_role_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    IAMclient = boto3.client("iam")
    IAM_cr_response = IAMclient.create_role(
        RoleName='eksNodeRole', AssumeRolePolicyDocument=json.dumps(node_role_trust_policy))
    print(IAM_cr_response)
    create_nodegroup_args['nodeRole'] = IAM_cr_response['Role']['Arn']
    try:
        IAMclient.attach_role_policy(RoleName='eksNodeRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy')
        IAMclient.attach_role_policy(RoleName='eksNodeRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly')
        IAMclient.attach_role_policy(RoleName='eksNodeRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy')
    except Exception as error:
        print(error)

def create_cluster():
    eks_client = boto3.client('eks')
    cc_response = eks_client.create_cluster(**create_cluster_args)
    cluster_status = eks_client.describe_cluster(name=create_cluster_args['name'])['cluster']['status']
    while cluster_status != 'ACTIVE':
        sleep(30)
        cluster_status = eks_client.describe_cluster(name=create_cluster_args['name'])['cluster']['status']
    print(f'Cluster Status is {cluster_status}')

def create_nodegroup():
    eks_client = boto3.client('eks')
    cng_response = eks_client.create_nodegroup(**create_nodegroup_args)


def clean_up():
    CFclient = boto3.client("cloudformation")
    CFclient.delete_stack(StackName="stochss-compute-vpc")

    IAMclient = boto3.client("iam")
    iam = boto3.resource('iam')
    eksClusterRole = iam.Role('eksClusterRole')
    try:
        eksClusterRole.detach_policy(
            PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
        eksClusterRole.delete()
    except IAMclient.exceptions.NoSuchEntityException as error:
        print("eksClusterRole already deleted.")
        pass
    else:
        print(error)
        pass
    try:
        eksNodeRole = iam.Role('eksNodeRole')
        for policy in eksNodeRole.attached_policies.all():
            policy.detach_role(RoleName='eksNodeRole')
        # add check to make sure all policies are detached by checking length of attached policies == 0
        eksNodeRole.delete()
    except IAMclient.exceptions.NoSuchEntityException as error:
        print("eksNodeRole already deleted.")
        pass
    else:
        print(error)
        pass

    EKSclient = boto3.client('eks')
    EKSclient.delete_nodegroup(clusterName=create_nodegroup_args['clusterName'], nodegroupName=create_nodegroup_args['nodegroupName'])
    # this will take some time so check to make sure it has completed
    EKSclient.delete_cluster(name=create_cluster_args['name'])
