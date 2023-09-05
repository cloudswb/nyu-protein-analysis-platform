#!/usr/bin/env python3
import os

import aws_cdk as cdk
from nyu_protein_website_deploy.config import config

from nyu_protein_website_deploy.nyu_protein_vpc_deploy_stack import NyuProteinVpcDeployStack

from nyu_protein_website_deploy.nyu_protein_rds_deploy_stack import NyuProteinRDSDeployStack
from nyu_protein_website_deploy.nyu_protein_neptune_deploy_stack import NyuProteinNeptuneDeployStack
from nyu_protein_website_deploy.nyu_protein_neptune_serverless_deploy_stack import NyuProteinNeptuneServerlessDeployStack


from nyu_protein_website_deploy.nyu_protein_cloudfront_s3_deploy_stack import NyuProteinCloudFrontS3DeployStack
from nyu_protein_website_deploy.nyu_protein_layer_lambda_deploy_stack import NyuProteinLayerLambdaDeployStack

app = cdk.App()

env = cdk.Environment(account=config.ACCT_ID, region=config.ACCT_REGION)
# env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),


vpc_stack = NyuProteinVpcDeployStack(app, "NyuProteinVpcDeployStack", env = env)
if(config.IS_SERVERLESS):
    neptune_stack = NyuProteinNeptuneServerlessDeployStack(app, 'NyuProteinNeptuneServerlessDeployStack', vpc_stack.vpc, env = env)
else:
    neptune_stack = NyuProteinNeptuneDeployStack(app, 'NyuProteinNeptuneDeployStack', vpc_stack.vpc, env = env)

rds_stack = NyuProteinRDSDeployStack(app, 'NyuProteinRDSDeployStack', vpc_stack.vpc, env = env)

NyuProteinCloudFrontS3DeployStack(app, "NyuProteinWebsiteDeployStack", env = env)
local_layer_stack = NyuProteinLayerLambdaDeployStack(app, 'NyuProteinLayerLambdaAGWDeployStack',vpc_stack.vpc, env = env)

# lambda_with_layer_stack = NyuProteinLambdaDeployStack(app, 'LambdaWithLayerStack', layer=local_layer_stack.pymysql_layer)
# api_gateway_stack = NyuProteinAGWDeployStack(app, 'ApiGatewayStack', function1=lambda_with_layer_stack.function1, function2=lambda_with_layer_stack.function2)

app.synth()