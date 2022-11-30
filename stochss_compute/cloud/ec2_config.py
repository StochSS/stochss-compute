import os


class EC2RemoteConfig:
    _AMIS = {
        'us-east-1': 'ami-09d3b3274b6c5d4aa',
        'us-east-2': 'ami-089a545a9ed9893b6',
        'us-west-1': 'ami-017c001a88dd93847',
        'us-west-2': 'ami-0d593311db5abb72b',
    }
    def __init__(self,
                suffix=None,
                vpc_name='sssc-vpc',
                subnet_name='sssc-subnet',
                security_group_name='sssc-sg',
                server_name='sssc-server',
                key_name='sssc-server-ssh-key',
                api_port=29681,
                region=None,
                ami=None,
                ):
        suffix = suffix or ''
        self.vpc_name = vpc_name + f'-{suffix}'
        self.subnet_name = subnet_name + f'-{suffix}'
        self.security_group_name = security_group_name + f'-{suffix}'
        self.server_name = server_name + f'-{suffix}'
        self.key_name = key_name + f'-{suffix}'
        self.api_port = api_port
        
        self.region = region
        self.ami = ami

class EC2LocalConfig:
    def __init__(self, 
                key_dir='./.sssc',
                key_name='sssc-server-ssh-key',
                status_file=None,
                key_type='ed25519',
                key_format='pem',
                ):
        self._key_dir = key_dir
        self._key_filename = f'{key_name}.{key_format}'
        self.key_type = key_type
        self.key_format = key_format
        self.key_path = os.path.abspath(os.path.join(self._key_dir, self._key_filename))
        self.status_file = status_file