#!/usr/bin/env python3
import os

import aws_cdk as cdk
from deploy.config import config

from deploy.protein_vpc_deploy_stack import ProteinDCVpcDeployStack

from deploy.protein_rds_deploy_stack import ProteinDCRDSDeployStack
from deploy.protein_neptune_deploy_stack import ProteinDCNeptuneDeployStack
from deploy.protein_neptune_serverless_deploy_stack import ProteinDCNeptuneServerlessDeployStack
from deploy.protein_neptune_notebook_deploy_stack import ProteinDCNeptuneNotebookDeployStack


from deploy.protein_website_cloudfront_deploy_stack import ProteinDCWebsiteCloudFrontDeployStack
from deploy.protein_website_s3_deploy_stack import ProteinDCWebsiteS3DeployStack
from deploy.protein_layer_lambda_deploy_stack import ProteinDCLayerLambdaDeployStack

app = cdk.App()

env = cdk.Environment(account=config.ACCT_ID, region=config.ACCT_REGION)


vpc_stack = ProteinDCVpcDeployStack(app, "ProteinDCVpcDeployStack", env = env)
if(config.IS_NEPTUNE_SERVERLESS):
    neptune_stack = ProteinDCNeptuneServerlessDeployStack(app, 'ProteinDCNeptuneServerlessDeployStack', vpc_stack.vpc, env = env)
else:
    neptune_stack = ProteinDCNeptuneDeployStack(app, 'ProteinDCNeptuneDeployStack', vpc_stack.vpc, env = env)
neptune_stack.add_dependency(vpc_stack)

neptune_notebook_stack = ProteinDCNeptuneNotebookDeployStack(app, 'ProteinDCNeptuneNotebookDeployStack', 
                                                              vpc_stack.vpc, 
                                                              neptune_stack.graph_db_ep, 
                                                              neptune_stack.graph_db_ep_port, 
                                                              neptune_stack.graph_db_attr_cluster_resource_id, 
                                                              env = env)
neptune_notebook_stack.add_dependency(neptune_stack)

rds_stack = ProteinDCRDSDeployStack(app, 'ProteinDCRDSDeployStack', vpc_stack.vpc, env = env)
rds_stack.add_dependency(neptune_notebook_stack)

lambda_stack = ProteinDCLayerLambdaDeployStack(app, 'ProteinDCLayerLambdaAGWDeployStack',vpc_stack.vpc, neptune_stack.graph_db_ep,rds_stack.rds_ep, env = env)
lambda_stack.add_dependency(rds_stack)

website_s3_stack = ProteinDCWebsiteS3DeployStack(app, "ProteinDCWebsiteS3DeployStack", env = env)
website_s3_stack.add_dependency(lambda_stack)

website_cf_stack = ProteinDCWebsiteCloudFrontDeployStack(app, "ProteinDCWebsiteCloudFrontDeployStack", website_s3_stack.origin_access_identity,env = env)
website_cf_stack.add_dependency(website_s3_stack)


app.synth()