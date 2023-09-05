#!/usr/bin/env python3
import os

import aws_cdk as cdk
from deploy.config import config

from deploy.nyu_protein_vpc_deploy_stack import NyuProteinVpcDeployStack

from deploy.nyu_protein_rds_deploy_stack import NyuProteinRDSDeployStack
from deploy.nyu_protein_neptune_deploy_stack import NyuProteinNeptuneDeployStack
from deploy.nyu_protein_neptune_serverless_deploy_stack import NyuProteinNeptuneServerlessDeployStack
from deploy.nyu_protein_neptune_notebook_deploy_stack import NyuProteinNeptuneNotebookDeployStack


from deploy.nyu_protein_cloudfront_s3_deploy_stack import NyuProteinCloudFrontS3DeployStack
from deploy.nyu_protein_layer_lambda_deploy_stack import NyuProteinLayerLambdaDeployStack

app = cdk.App()

env = cdk.Environment(account=config.ACCT_ID, region=config.ACCT_REGION)
# env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),


vpc_stack = NyuProteinVpcDeployStack(app, "NyuProteinVpcDeployStack", env = env)
if(config.IS_SERVERLESS):
    neptune_stack = NyuProteinNeptuneServerlessDeployStack(app, 'NyuProteinNeptuneServerlessDeployStack', vpc_stack.vpc, env = env)
else:
    neptune_stack = NyuProteinNeptuneDeployStack(app, 'NyuProteinNeptuneDeployStack', vpc_stack.vpc, env = env)
neptune_stack.add_dependency(vpc_stack)

neptune_notebook_stack = NyuProteinNeptuneNotebookDeployStack(app, 'NyuProteinNeptuneNotebookDeployStack', 
                                                              vpc_stack.vpc, 
                                                              neptune_stack.graph_db_ep, 
                                                              neptune_stack.graph_db_ep_port, 
                                                              neptune_stack.graph_db_attr_cluster_resource_id, 
                                                              env = env)
neptune_notebook_stack.add_dependency(neptune_stack)

rds_stack = NyuProteinRDSDeployStack(app, 'NyuProteinRDSDeployStack', vpc_stack.vpc, env = env)
rds_stack.add_dependency(neptune_notebook_stack)

website_stack = NyuProteinCloudFrontS3DeployStack(app, "NyuProteinWebsiteDeployStack", env = env)
website_stack.add_dependency(rds_stack)

lambda_stack = NyuProteinLayerLambdaDeployStack(app, 'NyuProteinLayerLambdaAGWDeployStack',vpc_stack.vpc, env = env)
lambda_stack.add_dependency(website_stack)

# lambda_with_layer_stack = NyuProteinLambdaDeployStack(app, 'LambdaWithLayerStack', layer=local_layer_stack.pymysql_layer)
# api_gateway_stack = NyuProteinAGWDeployStack(app, 'ApiGatewayStack', function1=lambda_with_layer_stack.function1, function2=lambda_with_layer_stack.function2)

app.synth()