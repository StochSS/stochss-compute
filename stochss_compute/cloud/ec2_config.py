class EC2RemoteConfig:
    def __init__(self, 
                vpc_name='sssc-vpc',
                subnet_prefix='sssc-subnet-',
                security_group_name='sssc-sg',
                server_name='sssc-server',
                key_name='sssc-root',
                key_path='./',
                api_port=29681,
                ami=None,
                ):
        self.vpc_name = vpc_name
        self.subnet_prefix = subnet_prefix
        self.security_group_name = security_group_name
        self.server_name = server_name
        self.key_name = key_name
        self.key_path = key_path
        self.api_port = api_port

        self.ami = ami

class EC2LocalConfig:
    def __init__(self, 
                key_path='./',
                key_name='sssc-root',
                status_file=None,
                ):
        self.key_path = key_path
        self.key_name = key_name
        self.status_file = status_file