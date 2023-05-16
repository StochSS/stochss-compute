class S3Config:
    '''
    Configuration for AWS Simple Storage Service
    '''
    def __init__(self,
                 instance_role_arn,
                 s3_bucket_uri,
                 ) -> None:
        self.instance_role_arn = instance_role_arn
        self.s3_bucket_uri = s3_bucket_uri
        