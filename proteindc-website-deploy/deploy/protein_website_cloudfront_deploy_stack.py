import aws_cdk as cdk
import boto3
import json
from deploy.config import config
from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    RemovalPolicy as removalPolicy,
    Stack,
)

class ProteinDCWebsiteCloudFrontDeployStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, origin_access_identity: cloudfront.OriginAccessIdentity, s3_bucket: s3.Bucket, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Define Cloudfront CDN that delivers from S3 bucket
        self.cdn = self._create_cdn(access_identity=origin_access_identity, s3_bucket = s3_bucket)

        cdk.CfnOutput(
            self, 
            'Website Domain Name',
            value=config.WEB_DOMAIN_NAME,
        )

        cdk.CfnOutput(
            self, 
            'Website Cloudfront Distribution Domain Name',
            value=self.cdn.distribution_domain_name,
        )

    def _create_cdn(self, access_identity, s3_bucket):
        """ Returns a CDN that delivers from a S3 bucket """
        if(config.WEB_CERT_ARN):
            return cloudfront.Distribution(
                self,
                'ProteinDataWebsiteDist',
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        s3_bucket,
                        origin_access_identity=access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
                ),
                domain_names = [config.WEB_DOMAIN_NAME],
                default_root_object=config.WEB_ROOT_FILE,
                certificate = acm.Certificate.from_certificate_arn(self, "domainCert", config.WEB_CERT_ARN)
            )
        else:
            return cloudfront.Distribution(
                self,
                'ProteinDataWebsiteDist',
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        s3_bucket,
                        origin_access_identity=access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY
                ),
                domain_names = [config.WEB_DOMAIN_NAME],
                default_root_object=config.WEB_ROOT_FILE,
            )
            
