import aws_cdk as cdk
from nyu_protein_website_deploy.config import Config

from constructs import Construct
from aws_cdk import (aws_apigateway as apigateway,
                     aws_s3 as s3,
                     aws_ec2 as ec2,
                     Stack,
                     aws_lambda as _lambda)

class NyuProteinLayerDeployStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pymysql_layer = _lambda.LayerVersion(self, 'pymysql',
            code=_lambda.Code.from_asset(path='./layers/pymysql'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='PyMySQL Lambda Layer'
        )

        SPARQLWrapper_layer = _lambda.LayerVersion(self, 'SPARQLWrapper',
            code=_lambda.Code.from_asset(path='./layers/SPARQLWrapper'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='SPARQLWrapper Lambda Layer'
        )

        # Create a VPC
        # vpc = ec2.Vpc(self, 'MyVpc', max_azs=2)  # Adjust properties as needed
        # existing_vpc = ec2.Vpc.from_vpc_attributes(self, "ExistingVPC", vpc_id=VPC_ID, availability_zones = ec2.get_available_zones(self))

        existing_vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id=Config.VPC_ID)
        
        timeout_seconds = 30

        # Define environment variables
        og_query_function_env_vars = {
            'DB_NAME': 'nyu-og',
            'PASSWORD': '4z(hFH-({u2Y*g:$BL{!D$Rp%H_!',
            'RDS_HOST': 'nyu-database.cluster-cnfpwwtkftli.us-east-1.rds.amazonaws.com',
            'USER_NAME': 'awsuser',
        }

        # Create Lambda functions using the uploaded layer
        og_query_function = _lambda.Function(self, 'og_query_function',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',  # Replace with your handler name
            code=_lambda.Code.from_asset('./nyu_protein_website_deploy/lambda/og_query'),  # Replace with your function1 code directory
            layers=[pymysql_layer],
            environment=og_query_function_env_vars,
            vpc=existing_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT),  # Adjust subnet type as needed
            timeout = cdk.Duration.seconds(timeout_seconds),
        )

        # Define environment variables
        protein_annotation_function_env_vars = {
            'SPARQL_ENDPOINT': 'https://nyu-neptune-instance-1.cnfpwwtkftli.us-east-1.neptune.amazonaws.com:8182/sparql',
        }

        protein_annotation_function = _lambda.Function(self, 'protein_annotation_function',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',  # Replace with your handler name
            code=_lambda.Code.from_asset('./nyu_protein_website_deploy/lambda/protein_annotation'),  # Replace with your function2 code directory
            layers=[SPARQLWrapper_layer],
            environment=protein_annotation_function_env_vars,
            vpc=existing_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT),  # Adjust subnet type as needed
            timeout = cdk.Duration.seconds(timeout_seconds),
        )

        # Create the REST API
        api = apigateway.RestApi(self, 'ProteinDataApi', rest_api_name='ProteinDataApi')

        # Create resources and methods for each Lambda function
        resource1 = api.root.add_resource('og_query_function')
        resource1.add_method('GET', apigateway.LambdaIntegration(og_query_function))

        resource2 = api.root.add_resource('protein_annotation_function')
        resource2.add_method('GET', apigateway.LambdaIntegration(protein_annotation_function))