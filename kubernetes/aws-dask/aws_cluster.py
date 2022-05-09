import boto3
from botocore.config import Config
import os

# class AWSCluster():
#     def __init__(self) -> None:
#         super().__init__()
os.environ['AWS_CONFIG_FILE'] = './.aws/config'
os.environ['AWS_PROFILE'] = 'AWS_PROFILE=ClusterCreate'
config = Config()
CFclient = boto3.client("cloudformation",config=config)
def create_vpc():
    # CFclient.create_stack(
    #     TemplateURL="https://s3.us-west-2.amazonaws.com/amazon-eks/cloudformation/2020-10-29/amazon-eks-vpc-private-subnets.yaml", 
    #     StackName="stochss-compute-vpc")
    CFclient.create_stack(
        StackName="stochss-compute-vpc"
    )

def clean_up():
    CFclient.delete_stack(StackName="stochss-compute-vpc")