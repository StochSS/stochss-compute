import json
import boto3
import botocore.exceptions
from time import sleep

create_cluster_args = { 'name':'stochss-compute-dask' }
create_nodegroup_args = { 'clusterName':'stochss-compute-dask', 'nodegroupName': 'dask-0', 'scalingConfig': {'minSize': 2, 'maxSize': 5, 'desiredSize': 3}, 'instanceTypes': ['t3.micro'] }         
vpc_stack_attributes = {}
def init_vpc():
    print("Creating CloudFormation VPC stack.")
    CFclient = boto3.client('cloudformation')
    vpc_response = CFclient.create_stack(TemplateURL='https://s3.us-west-2.amazonaws.com/amazon-eks/cloudformation/2020-10-29/amazon-eks-vpc-private-subnets.yaml', StackName='stochss-compute-vpc')
    vpc_stack_attributes['stackId'] = vpc_response['StackId']
    cloudformation = boto3.resource('cloudformation')
    vpc_stack = cloudformation.Stack('stochss-compute-vpc')
    while vpc_stack.stack_status != 'CREATE_COMPLETE':
        sleep(10)
        vpc_stack = cloudformation.Stack('stochss-compute-vpc')
    print(f'CloudFormation VPC stack "{vpc_stack.name}" successfully created.')
    vpc_id = vpc_stack.Resource('VPC').physical_resource_id
    sg_id = vpc_stack.Resource('ControlPlaneSecurityGroup').physical_resource_id
    ec2 = boto3.resource('ec2')
    subnet_ids = [subnet.id for subnet in ec2.Vpc(vpc_id).subnets.all()]
    create_cluster_args['resourcesVpcConfig'] = {'subnetIds':subnet_ids,'securityGroupIds':[sg_id]}
    create_nodegroup_args['subnets'] = subnet_ids


def init_cluster_role():
    roleName = 'eksClusterRole'
    print(f'Creating Cluster Role "{roleName}".')
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
    IAMclient = boto3.client('iam')
    iam = boto3.resource('iam')
    IAM_cr_response = IAMclient.create_role(RoleName='eksClusterRole', AssumeRolePolicyDocument=json.dumps(cluster_role_trust_policy))
    create_cluster_args['roleArn'] = IAM_cr_response['Role']['Arn']
    try:
        IAM_ar_response =  IAMclient.attach_role_policy(
            RoleName='eksClusterRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
    except Exception as error :
        print(error)
    role_arn = iam.Role(roleName).arn
    print(f'Cluster Role "{role_arn}" successfully created.')

def init_node_role():
    roleName = 'eksNodeRole'
    print(f'Creating Node Role "{roleName}".')
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
    iam = boto3.resource('iam')
    IAM_cr_response = IAMclient.create_role(
        RoleName='eksNodeRole', AssumeRolePolicyDocument=json.dumps(node_role_trust_policy))
    create_nodegroup_args['nodeRole'] = IAM_cr_response['Role']['Arn']
    try:
        IAMclient.attach_role_policy(RoleName='eksNodeRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy')
        IAMclient.attach_role_policy(RoleName='eksNodeRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly')
        IAMclient.attach_role_policy(RoleName='eksNodeRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy')
    except Exception as error:
        print(error)
    role_arn = iam.Role(roleName).arn
    print(f'Cluster Role "{role_arn}" successfully created.')

def init_cluster():
    print("Creating EKS Cluster with args:")
    print(json.dumps(create_cluster_args, indent=4))
    eks_client = boto3.client('eks')
    clusterName = create_cluster_args['name']
    cc_response = eks_client.create_cluster(**create_cluster_args)
    cluster_status = eks_client.describe_cluster(name=clusterName)['cluster']['status']
    while cluster_status != 'ACTIVE':
        sleep(30)
        cluster_status = eks_client.describe_cluster(name=clusterName)['cluster']['status']
        print(f'Cluster "{clusterName}" status is "{cluster_status}".')
    print(f'Cluster "{clusterName}" successfully created.')

def init_nodegroup():
    print("Creating Nodegroup with args:")
    print(json.dumps(create_nodegroup_args, indent=4))
    eks_client = boto3.client('eks')
    cng_response = eks_client.create_nodegroup(**create_nodegroup_args)
    clusterName = create_nodegroup_args['clusterName']
    nodegroupName = create_nodegroup_args['nodegroupName']
    nodegroup_status = eks_client.describe_nodegroup(clusterName=clusterName, nodegroupName=nodegroupName)['nodegroup']['status']
    while nodegroup_status != 'ACTIVE':
        sleep(30)
        nodegroup_status = eks_client.describe_nodegroup(clusterName=clusterName, nodegroupName=nodegroupName)['nodegroup']['status']
        print(f'Nodegroup "{nodegroupName}" status is "{nodegroup_status}".')
    print(f'Nodegroup "{nodegroupName}" successfully created.')

def tear_down_vpc():
    stackName = 'stochss-compute-vpc'
    StackId = vpc_stack_attributes['stackId']
    print(f'Deleting CloudFormation VPC stack "{stackName}".')
    CFclient = boto3.client("cloudformation")
    
    CFclient.delete_stack(StackName=stackName)
    stack_status = CFclient.describe_stacks(StackName=StackId)['Stacks'][0]['StackStatus']
    while stack_status != 'DELETE_COMPLETE':
        if stack_status == 'DELETE_FAILED':
            raise Exception('Unknown error. CloudFormation VPC stack deletion failed.')
        sleep(10)
        stack_status = CFclient.describe_stacks(StackName=StackId)['Stacks'][0]['StackStatus']
        continue
    print(f'CloudFormation VPC stack "{stackName}" successfully deleted.')

def tear_down_roles():
    clusterRoleName = 'eksClusterRole'
    print(f'Deleting Role "{clusterRoleName}".')
    
    noSuchEntity = boto3.client("iam").exceptions.NoSuchEntityException
    iam = boto3.resource('iam')
    try:
        eksClusterRole = iam.Role(clusterRoleName)
        attached_policies = list(eksClusterRole.attached_policies.all())
        while len(attached_policies) != 0:
            try:
                eksClusterRole.detach_policy(
                    PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
            except noSuchEntity:
                print(f'AmazonEKSClusterPolicy already detached.')
            sleep(1)
            attached_policies = list(eksClusterRole.attached_policies.all())
        eksClusterRole.delete()
    except noSuchEntity as error:
        print(f'"{clusterRoleName}" already deleted.')
    except BaseException as error:
        print(f'Unexpected error. "{clusterRoleName}" deletion unsuccessful.')
        print(error)
    else:
        print(f'"{clusterRoleName}" successfully deleted.')

    nodeRoleName = 'eksNodeRole'
    print(f'Deleting Role "{nodeRoleName}".')
    try:
        eksNodeRole = iam.Role(nodeRoleName)
        attached_policies = list(eksNodeRole.attached_policies.all())
        while len(attached_policies) != 0:
            for policy in attached_policies:
                try:
                    policy.detach_role(RoleName=nodeRoleName)
                except noSuchEntity:
                    print(f"{policy.policy_name} already detached.")
            sleep(1)
            attached_policies = list(eksNodeRole.attached_policies.all())
        eksNodeRole.delete()
    except noSuchEntity as error:
        print(f'"{nodeRoleName}" already deleted.')
    except BaseException as error:
        print(f'Unexpected error. "{nodeRoleName}" deletion unsuccessful.')
        print(error)
    else:
        print(f'"{nodeRoleName}" successfully deleted.')

def tear_down_nodegroup():
    clusterName = create_nodegroup_args['clusterName']
    nodegroupName = create_nodegroup_args['nodegroupName']
    print(f"Deleting Nodegroup {nodegroupName}")
    EKSclient = boto3.client('eks')
    resourceNotFound = EKSclient.exceptions.ResourceNotFoundException
    try:
        EKSclient.delete_nodegroup(clusterName=clusterName, nodegroupName=nodegroupName)
    except resourceNotFound:
        print(f"Nodegroup {nodegroupName} already deleted.")
    else:
        while True:
            try:
                EKSclient.describe_nodegroup(clusterName=clusterName,nodegroupName=nodegroupName)
                sleep(10)
                continue
            except resourceNotFound:
                break
        print(f"Nodegroup {nodegroupName} successfully deleted.")
    
def tear_down_cluster():
    name = create_cluster_args['name']
    print(f"Deleting Cluster {name}")
    EKSclient = boto3.client('eks')
    resourceNotFound = EKSclient.exceptions.ResourceNotFoundException
    try:
        EKSclient.delete_cluster(name=name)
    except resourceNotFound:
        print(f"Cluster {name} already deleted.")
    else:
        while True:
            try:
                EKSclient.describe_cluster(name=name)
                sleep(10)
                continue
            except resourceNotFound:
                break
        print(f"Cluster {name} successfully deleted.")

def create_cluster():
    init_vpc()
    init_cluster_role()
    init_cluster()
    init_node_role()
    init_nodegroup()

def tear_down():
    tear_down_nodegroup()
    tear_down_cluster()
    tear_down_vpc()
    tear_down_roles()
