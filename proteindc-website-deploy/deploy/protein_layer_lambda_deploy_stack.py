import aws_cdk as cdk
from deploy.config import config

from constructs import Construct
from aws_cdk import (aws_apigateway as apigateway,
                     aws_s3 as s3,
                     aws_ec2 as ec2,
                     Stack,
                     aws_lambda as _lambda)
import subprocess
import json
class ProteinDCLayerLambdaDeployStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str,vpc: ec2.Vpc, neptune_ep: str, rds_ep: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        existing_vpc = vpc


        pymysql_layer = _lambda.LayerVersion(self, 'pymysql',
            code=_lambda.AssetCode.from_asset(path='./layers/pymysql'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='PyMySQL Lambda Layer'
        )

        SPARQLWrapper_layer = _lambda.LayerVersion(self, 'SPARQLWrapper',
            code=_lambda.Code.from_asset(path='./layers/SPARQLWrapper'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='SPARQLWrapper Lambda Layer'
        )


        timeout_seconds = 30

        # Define environment variables
        og_query_function_env_vars = {
            'DB_NAME': config.MYSQL_DEFAULT_DB_NAME,
            'PASSWORD': config.MYSQL_PASSWORD,
            'RDS_HOST': rds_ep,
            'USER_NAME': config.MYSQL_USER_NAME,
        }

        # Create Lambda functions using the uploaded layer
        og_query_function = _lambda.Function(self, 'og_query_function',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',  # Replace with your handler name
            code=_lambda.Code.from_asset('./deploy/lambda/og_query'),  # Replace with your function1 code directory
            layers=[pymysql_layer],
            environment=og_query_function_env_vars,
            vpc=existing_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT),  # Adjust subnet type as needed
            timeout = cdk.Duration.seconds(timeout_seconds),
        )

        # Define environment variables
        protein_annotation_function_env_vars = {
            'SPARQL_ENDPOINT': neptune_ep,
        }

        protein_annotation_function = _lambda.Function(self, 'protein_annotation_function',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',  # Replace with your handler name
            code=_lambda.Code.from_asset('./deploy/lambda/protein_annotation'),  # Replace with your function2 code directory
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

        self.api_url = api.url
        self.update_website_config()

    
    def update_website_config(self):

        file_path = '../web/config.js'

        # Open the file in append mode ('a')
        with open(file_path, 'a') as file:
            file.write("\n")  # Add a newline before appending
            file.write("""const config = {
                apiEndpoint: '{self.api_url}'
            };""")
            file.write("\n") 
            file.write("export default config;") 

        print(f'Content has been appended to the file "{file_path}".')