class EC2RemoteConfig:
    _AMIS = {
        'us-east-1': 'ami-09d3b3274b6c5d4aa',
        'us-east-2': 'ami-089a545a9ed9893b6',
        'us-west-1': 'ami-017c001a88dd93847',
        'us-west-2': 'ami-0d593311db5abb72b',
    }
    def __init__(self, 
                vpc_name='sssc-vpc',
                subnet_prefix='sssc-subnet-',
                security_group_name='sssc-sg',
                server_name='sssc-server',
                key_name='sssc-root',
                key_path='./',
                api_port=29681,
                region=None,
                ami=None,
                ):
        self.vpc_name = vpc_name
        self.subnet_prefix = subnet_prefix
        self.security_group_name = security_group_name
        self.server_name = server_name
        self.key_name = key_name
        self.key_path = key_path
        self.api_port = api_port
        
        self.region = region
        self.ami = ami

class EC2LocalConfig:
    def __init__(self, 
                key_path='.sssc/',
                key_name='sssc-root',
                status_file=None,
                ):
        self.key_path = key_path
        self.key_name = key_name
        self.status_file = status_file