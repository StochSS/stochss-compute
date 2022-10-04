class ResourceException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print('Missing or misconfigured resources. You need to call clean_up().')

class EC2ImportException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print('StochSS-Compute on EC2 requires boto3 and paramiko to be installed.\nTry: pip install boto3 paramiko')

