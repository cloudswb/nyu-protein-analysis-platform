#!/usr/bin/env python3
import os

import aws_cdk as cdk

# from nyu_protein_website_deploy.nyu_protein_cloudfront_s3_deploy_stack import NyuProteinCloudFrontS3DeployStack
# from nyu_protein_website_deploy.nyu_protein_agw_deploy_stack import NyuProteinAGWDeployStack
from nyu_protein_website_deploy.nyu_protein_database_deploy_stack import NyuProteinDatabaseDeployStack
from nyu_protein_website_deploy.nyu_protein_layer_deploy_stack import NyuProteinLayerDeployStack

app = cdk.App()
# NyuProteinCloudFrontS3DeployStack(app, "NyuProteinWebsiteDeployStack",
#     # If you don't specify 'env', this stack will be environment-agnostic.
#     # Account/Region-dependent features and context lookups will not work,
#     # but a single synthesized template can be deployed anywhere.

#     # Uncomment the next line to specialize this stack for the AWS Account
#     # and Region that are implied by the current CLI configuration.

#     #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

#     # Uncomment the next line if you know exactly what Account and Region you
#     # want to deploy the stack to. */

#     #env=cdk.Environment(account='123456789012', region='us-east-1'),

#     # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
#     )


env = cdk.Environment(account="629244530291", region="us-east-1")

local_layer_stack = NyuProteinLayerDeployStack(app, 'NyuProteinLayerLambdaAGWDeployStack', env = env)
database_stack = NyuProteinDatabaseDeployStack(app, 'NyuProteinDatabaseDeployStack', env = env)
# lambda_with_layer_stack = NyuProteinLambdaDeployStack(app, 'LambdaWithLayerStack', layer=local_layer_stack.pymysql_layer)
# api_gateway_stack = NyuProteinAGWDeployStack(app, 'ApiGatewayStack', function1=lambda_with_layer_stack.function1, function2=lambda_with_layer_stack.function2)

app.synth()
