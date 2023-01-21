'''
stochss_compute.cloud.exceptions
'''
class ResourceException(Exception):
    '''
    Misconfigured or out-of-date resources detected in the cluster setup.
    '''
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print('Missing or misconfigured resources.')

class EC2ImportException(Exception):
    '''
    Some extra dependencies are required for EC2.
    '''
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print('StochSS-Compute on EC2 requires boto3 and paramiko to be installed.\nTry: pip install boto3 paramiko')

class EC2Exception(Exception):
    '''
    General exception class.
    '''
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
