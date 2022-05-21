from typing import List, Union
import boto3
import os
import pprint

p = pprint.PrettyPrinter(indent=1)

class SSSCEC2:

    class SSHKey:
        def __init__(self, name) -> None:
            self.name = name
            
    class Instance:
        def __init__(self, id) -> None:
            resource = boto3.resource('ec2')
            self._remote = resource.Instance(id)

        def state(self) -> str:
            self._remote.load()
            return self._remote.state
        
        def reboot(self) -> None:
            self._remote.reboot()

        def start(self) -> None:
            self._remote.start()
            self._remote.wait_until_running()
        
        def stop(self) -> None:
            self._remote.stop()
            self._remote.wait_until_stopped()

        def terminate(self) -> None:
            self._remote.terminate()
            self._remote.wait_until_terminated()

    def __init__(self) -> None:
        self.client = boto3.client('ec2')
        self.resources = boto3.resource('ec2')
        self.returns = {}
        self.rootKey = self.SSHKey('sssc-root')
        self.instances = []
        

    def create_root_key(self, savePath='./', keyType='ed25519', keyFormat='pem') -> SSHKey:
        valid_formats = {'pem', 'ppk'}
        if keyFormat not in valid_formats:
            raise ValueError(f'keyFormat must be one of {valid_formats}.')
        valid_types = {'ed25519', 'rsa'}
        if keyType not in valid_types:
            raise ValueError(f'keyType must be one of {valid_types}.')

        key_path = f'{savePath}{self.rootKey.name}.{keyFormat}'
        key = open(key_path, 'x')
        response = self.client.create_key_pair(KeyName=self.rootKey.name, KeyType=keyType, KeyFormat=keyFormat)
        key.write(response['KeyMaterial'])
        key.close()
        os.chmod(key_path, 0o400)

        self.rootKey.fingerprint = response['KeyFingerprint']
        self.rootKey.id = response['KeyPairId']
        self.rootKey.path = key_path
        self.rootKey.type = keyType
        self.rootKey.format = keyFormat
        return self.rootKey

    def delete_root_key(self) -> None:
        self.client.delete_key_pair(KeyName=self.rootKey.name)

    def launch_instances(self, name='stochss-compute', imageId='ami-0fa49cc9dc8d62c84', instanceType='t3.micro', minCount=1, maxCount=1) -> Union[List[str], str]:
        valid_types = {'stochss-compute', 'scheduler', 'worker'}
        if name not in valid_types:
            raise ValueError(f'"name" must be one of {valid_types}.')
        kwargs = {
            'ImageId': imageId, 
            'InstanceType': instanceType,
            'KeyName': self.rootKey.name,
            'MinCount': minCount, 
            'MaxCount': maxCount,
            }
        response = self.client.run_instances(**kwargs)
        self.returns['launch'] = response
        self.security_group = response['Instances'][0]['SecurityGroups'][0]['GroupId']
        instance_ids = []
        for instance in response['Instances']:
            instance_ids.append(instance['InstanceId'])
        instances = []
        for i, id in enumerate(instance_ids):
            instance = self.resources.Instance(id)
            instance.wait_until_running()
            print(f'Instance "{id}" is now ready.')
            # TODO find out how to best refactor this
            _instance = self.Instance(id)
            if name =='worker':
                _instance.name = f'sssc-{name}-{i}'
            elif name == 'scheduler':
                _instance.name = f'sssc-{name}'
            else:
                _instance.name = name
            _instance.architechture = instance.architecture
            _instance.cores = instance.cpu_options['CoreCount']
            _instance.threads_per_core = instance.cpu_options['ThreadsPerCore']
            _instance.image_id = instance.image_id
            _instance.instance_type = instance.instance_type
            _instance.key_name = instance.key_name
            _instance.launch_time = instance.launch_time
            _instance.availability_zone = instance.placement['AvailabilityZone']
            _instance.platform = instance.platform_details
            _instance.private_dns_name = instance.private_dns_name
            _instance.private_ip_address = instance.private_ip_address
            _instance.public_dns_name = instance.public_dns_name
            _instance.public_ip_address = instance.public_ip_address
            _instance.root_device_name = instance.root_device_name
            _instance.root_device_type = instance.root_device_type
            # keep it simple, only allow one security group (not sure how it would work with multiple)
            _instance.security_group_name = instance.security_groups[0]['GroupName']
            _instance.security_group_id = instance.security_groups[0]['GroupId']
            _instance.subnet_id = instance.subnet_id
            # virtualization type?
            _instance.vpc_id = instance.vpc_id

            instances.append(_instance)
        self.instances.extend(instances)

        if len(instances) == 1:
            return instances[0]
        if len(instances) > 1:
            return instances

    def terminate_instances(self) -> None:
        describe_instances = self.client.describe_instances()
        instance_ids = []
        for reservation in describe_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        print(instance_ids)
        self.client.terminate_instances(InstanceIds=instance_ids)

    def get_running_instances() -> List[str]:
        kwargs = {
            'Filters':[
                {
                    'Name':'instance-state-name',
                    'Values':[
                        'running'
                    ]
                }
            ]
        }
        client = boto3.client('ec2')
        running_instances = client.describe_instances(**kwargs)
        instance_ids = []
        for reservation in running_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        return instance_ids

    def get_public_DNS(self, instance_id) -> str:
        self.resources = boto3.resource('ec2')
        instance = self.resources.Instance(instance_id)
        return instance.public_dns_name

        