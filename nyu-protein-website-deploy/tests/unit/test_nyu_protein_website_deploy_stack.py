import aws_cdk as core
import aws_cdk.assertions as assertions

from nyu_protein_website_deploy.nyu_protein_website_deploy_stack import NyuProteinCloudFrontS3DeployStack

# example tests. To run these tests, uncomment this file along with the example
# resource in nyu_protein_website_deploy/nyu_protein_website_deploy_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = NyuProteinCloudFrontS3DeployStack(app, "nyu-protein-website-deploy")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
