class ResourceException(Exception):
    def __init__(self):
        super().__init__('Missing or misconfigured resources.')

class EC2ImportException(Exception):
    def __init__(self):
        super().__init__('StochSS-Compute on EC2 requires boto3 and paramiko to be installed.\nTry: pip install boto3 paramiko')

class EC2Exception(Exception):
    def __init__(self):
        super().__init__()

