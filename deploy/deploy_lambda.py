import boto3
import zipfile
import os
import subprocess
from botocore.config import Config
from botocore.exceptions import ClientError
from datetime import datetime

class LambdaDeployer():

    def __init__(self, bucket_name):
        self.s3_client = boto3.client('s3')
        self.lambda_client = boto3.client('lambda')
        self.bucket_name = bucket_name
        
    def install_dependencies(self, requirements_file, target_dir):
        subprocess.check_call(['pip', 'install', '--no-deps', '-r', requirements_file, '-t', target_dir])

    def create_zip_file(self, zip_name, source_dirs):
        with zipfile.ZipFile(zip_name, 'w') as z:
            for source_dir in source_dirs:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        z.write(file_path, arcname)
                
    def upload_to_s3(self, zip_file, s3_key):
        self.s3_client.upload_file(zip_file, self.bucket_name, s3_key)
    
    def check_lambda_function_exists(self, function_name):
        try:
            self.lambda_client.get_function(FunctionName=function_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            else:
                raise e

    def create_lambda_function(self, function_name, role_arn, handler, s3_bucket, s3_key,environment_variables,layers):
        response = self.lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.10',
            Role=role_arn,
            Handler=handler,
            Code={
                'S3Bucket': s3_bucket,
                'S3Key': s3_key
            },
            Environment={
                'Variables': environment_variables
            },
            Layers=layers,
            Publish=True,
            Timeout=300,  # 超时时间，单位为秒
            MemorySize=128  # 内存大小，单位为MB
        )
        return response

    def update_lambda_function_code(self, function_name, s3_bucket, s3_key):
        response = self.lambda_client.update_function_code(
            FunctionName=function_name,
            S3Bucket=s3_bucket,
            S3Key=s3_key,
            Publish=True
        )
        return response

    def create_lambda_layer(self, layer_name, zip_file, description, runtimes):
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        layer_dir = os.path.join(root_path, 'layer')
        target_dir = os.path.join(layer_dir, 'python')
        requirements_file = os.path.join(root_path, 'requirements.layer.txt')

        # self.install_dependencies(requirements_file, target_dir)
        # self.create_zip_file(zip_file, [layer_dir])
        
        s3_key = f'layer/{zip_file}'
        print(f"uploading new layers: {zip_file} to s3://{self.bucket_name}/{s3_key}")
        # self.upload_to_s3(zip_file=zip_file, s3_key=s3_key)
            
        response = self.lambda_client.publish_layer_version(
            LayerName=layer_name,
            Description=description,
            Content={
                'S3Bucket': self.bucket_name,
                'S3Key': s3_key
            },
            CompatibleRuntimes=runtimes
        )
        return response

    def get_latest_layer_version_arn(self, layer_name):        
        response = self.lambda_client.list_layer_versions(
            LayerName=layer_name
        )
        
        # 获取最新版本的 ARN
        if 'LayerVersions' in response and len(response['LayerVersions']) > 0:
            latest_version = response['LayerVersions'][0]
            return latest_version['LayerVersionArn']
        else:
            return None

    def get_dependences_layers(self, force_install = False):
        layer_name = 'won2free_dependences'
            
        layer_arn = self.get_latest_layer_version_arn(layer_name)
        if layer_arn is None or force_install:
            zip_file = 'layer.zip'
            description = 'Won2free custom dependencies'
            runtimes = ['python3.10']
            response = self.create_lambda_layer(layer_name, zip_file, description, runtimes)
            layer_arn = response.get('LayerVersionArn')
            print(f"new layers created, arn: {layer_arn}")
        return [layer_arn]

    def deploy(self, lambda_dir='lambda/bot', fun_name='wot2free_tgbot', handler = 'lambda_function.lambda_handler'):
        
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        lambda_dir = os.path.join(root_path, lambda_dir)
        source_dir = os.path.join(root_path, 'src')
        
        
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M')
        zip_file = f'{fun_name}-{timestamp}.zip'
        self.create_zip_file(zip_file, [lambda_dir, source_dir])
        
        s3_key = f"lambda/{zip_file}"
        self.upload_to_s3(zip_file, s3_key)

        if self.check_lambda_function_exists(fun_name):
            response = self.update_lambda_function_code(
                function_name=fun_name,
                s3_bucket=self.bucket_name,
                s3_key=s3_key)
        else:
            # 创建 Lambda 函数
            role_arn = os.getenv('ROLE_ARN')  
            layers = self.get_dependences_layers() 
            environment_variables = {
                'QUEUE_NAME': os.getenv('QUEUE_NAME'),
                'TG_TOKEN': os.getenv('TG_TOKEN')
            }
            response = self.create_lambda_function(
                function_name=fun_name,
                role_arn=role_arn,
                handler=handler,
                s3_bucket=self.bucket_name,
                s3_key=s3_key,
                environment_variables=environment_variables,
                layers=layers
            )
        print(response)

if __name__ == "__main__":
    deployer = LambdaDeployer(bucket_name='won2free-lambda')
        
    deployer.get_dependences_layers(True)
    
    deployer.deploy(lambda_dir='lambda/reactor', 
                    fun_name='won2free_reactor', 
                    handler = 'lambda_function.lambda_handler')
    
    deployer.deploy(lambda_dir='lambda/job', 
                    fun_name='won2free_job_gird_check', 
                    handler = 'grid_check.lambda_handler')