#!/usr/bin/env python3
import os

import aws_cdk as cdk

from nyu_protein_website_deploy.nyu_protein_cloudfront_s3_deploy_stack import NyuProteinCloudFrontS3DeployStack
# from nyu_protein_website_deploy.nyu_protein_agw_deploy_stack import NyuProteinAGWDeployStack
# from nyu_protein_website_deploy.nyu_protein_database_deploy_stack import NyuProteinDatabaseDeployStack
from nyu_protein_website_deploy.nyu_protein_layer_lambda_deploy_stack import NyuProteinLayerLambdaDeployStack

app = cdk.App()

env = cdk.Environment(account="629244530291", region="us-east-1")
# env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

NyuProteinCloudFrontS3DeployStack(app, "NyuProteinWebsiteDeployStack", env = env)
local_layer_stack = NyuProteinLayerLambdaDeployStack(app, 'NyuProteinLayerLambdaAGWDeployStack', env = env)
# database_stack = NyuProteinDatabaseDeployStack(app, 'NyuProteinDatabaseDeployStack', env = env)
# lambda_with_layer_stack = NyuProteinLambdaDeployStack(app, 'LambdaWithLayerStack', layer=local_layer_stack.pymysql_layer)
# api_gateway_stack = NyuProteinAGWDeployStack(app, 'ApiGatewayStack', function1=lambda_with_layer_stack.function1, function2=lambda_with_layer_stack.function2)

app.synth()