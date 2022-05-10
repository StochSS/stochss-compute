import json
import boto3
from botocore.config import Config
from time import sleep

create_cluster_args = {'name':'stochss-compute-dask' }                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          {'Key': 'aws:cloudformation:stack-id', 'Value': 'arn:aws:cloudformation:us-east-2:946980283210:stack/stochss-compute-vpc/f590a3c0-d079-11ec-98ac-06b3fb62fc82'}, {'Key': 'Name', 'Value': 'stochss-compute-vpc-PublicSubnet02'}, {'Key': 'kubernetes.io/role/elb', 'Value': '1'}], 'SubnetArn': 'arn:aws:ec2:us-east-2:946980283210:subnet/subnet-0e50b882afd8e9a82', 'EnableDns64': False, 'Ipv6Native': False, 'PrivateDnsNameOptionsOnLaunch': {'HostnameType': 'ip-name', 'EnableResourceNameDnsARecord': False, 'EnableResourceNameDnsAAAARecord': False}}, {'AvailabilityZone': 'us-east-2b', 'AvailabilityZoneId': 'use2-az2', 'AvailableIpAddressCount': 16379, 'CidrBlock': '192.168.192.0/18', 'DefaultForAz': False, 'MapPublicIpOnLaunch': False, 'MapCustomerOwnedIpOnLaunch': False, 'State': 'available', 'SubnetId': 'subnet-0f7f35da057ed404b', 'VpcId': 'vpc-06b063844266c6689', 'OwnerId': '946980283210', 'AssignIpv6AddressOnCreation': False, 'Ipv6CidrBlockAssociationSet': [], 'Tags': [{'Key': 'aws:cloudformation:logical-id', 'Value': 'PrivateSubnet02'}, {'Key': 'kubernetes.io/role/internal-elb', 'Value': '1'}, {'Key': 'Name', 'Value': 'stochss-compute-vpc-PrivateSubnet02'}, {'Key': 'aws:cloudformation:stack-name', 'Value': 'stochss-compute-vpc'}, {'Key': 'aws:cloudformation:stack-id', 'Value': 'arn:aws:cloudformation:us-east-2:946980283210:stack/stochss-compute-vpc/f590a3c0-d079-11ec-98ac-06b3fb62fc82'}], 'SubnetArn': 'arn:aws:ec2:us-east-2:946980283210:subnet/subnet-0f7f35da057ed404b', 'EnableDns64': False, 'Ipv6Native': False, 'PrivateDnsNameOptionsOnLaunch': {'HostnameType': 'ip-name', 'EnableResourceNameDnsARecord': False, 'EnableResourceNameDnsAAAARecord': False}}, {'AvailabilityZone': 'us-east-2b', 'AvailabilityZoneId': 'use2-az2', 'AvailableIpAddressCount': 4091, 'CidrBlock': '172.31.16.0/20', 'DefaultForAz': True, 'MapPublicIpOnLaunch': True, 'MapCustomerOwnedIpOnLaunch': False, 'State': 'available', 'SubnetId': 'subnet-02075554becf553f7', 'VpcId': 'vpc-013586ead6b0893cd', 'OwnerId': '946980283210', 'AssignIpv6AddressOnCreation': False, 'Ipv6CidrBlockAssociationSet': [], 'SubnetArn': 'arn:aws:ec2:us-east-2:946980283210:subnet/subnet-02075554becf553f7', 'EnableDns64': False, 'Ipv6Native': False, 'PrivateDnsNameOptionsOnLaunch': {'HostnameType': 'ip-name', 'EnableResourceNameDnsARecord': False, 'EnableResourceNameDnsAAAARecord': False}}, {'AvailabilityZone': 'us-east-2c', 'AvailabilityZoneId': 'use2-az3', 'AvailableIpAddressCount': 4091, 'CidrBlock': '172.31.32.0/20', 'DefaultForAz': True, 'MapPublicIpOnLaunch': True, 'MapCustomerOwnedIpOnLaunch': False, 'State': 'available', 'SubnetId': 'subnet-0d84a1341c1e602e3', 'VpcId': 'vpc-013586ead6b0893cd', 'OwnerId': '946980283210', 'AssignIpv6AddressOnCreation': False, 'Ipv6CidrBlockAssociationSet': [], 'SubnetArn': 'arn:aws:ec2:us-east-2:946980283210:subnet/subnet-0d84a1341c1e602e3', 'EnableDns64': False, 'Ipv6Native': False, 'PrivateDnsNameOptionsOnLaunch': {'HostnameType': 'ip-name', 'EnableResourceNameDnsARecord': False, 'EnableResourceNameDnsAAAARecord': False}}], 'ResponseMetadata': {'RequestId': '00d5cfd9-2014-45b9-aa2c-eccfbedd81f8', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '00d5cfd9-2014-45b9-aa2c-eccfbedd81f8', 'cache-control': 'no-cache, no-store', 'strict-transport-security': 'max-age=31536000; includeSubDomains', 'vary': 'accept-encoding', 'content-type': 'text/xml;charset=UTF-8', 'transfer-encoding': 'chunked', 'date': 'Tue, 10 May 2022 16:20:07 GMT', 'server': 'AmazonEC2'}, 'RetryAttempts': 0}}

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
    vpc_id = vpc_stack.Resource('VPC').physical_resource_id
    sg_id = vpc_stack.Resource('ControlPlaneSecurityGroup').physical_resource_id
    print(vpc_id)
    ec2 = boto3.resource('ec2')
    subnet_ids = [subnet.id for subnet in ec2.Vpc(vpc_id).subnets.all()]
    create_cluster_args['resourcesVpcConfig'] = {'subnetIds':subnet_ids,'securityGroupIds':[sg_id]}
    print(create_cluster_args)


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
    try:
        IAM_ar_return =  IAMclient.attach_role_policy(
            RoleName='eksClusterRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
    except Exception as error :
        print(error)

    print(IAM_ar_return)

def create_cluster():
    eks_client = boto3.client('eks')
    eks_client.create_cluster(**create_cluster_args)
    pass

def clean_up():
    CFclient = boto3.client("cloudformation")
    CFclient.delete_stack(StackName="stochss-compute-vpc")
    iam = boto3.resource('iam')
    eksClusterRole = iam.Role("eksClusterRole")
    eksClusterRole.detach_policy(
        PolicyArn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy')
    eksClusterRole.delete()