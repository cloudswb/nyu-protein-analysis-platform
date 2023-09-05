import aws_cdk as cdk
from deploy.config import config
from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    RemovalPolicy as removalPolicy,
)
# from packages.aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3

class NyuProteinCloudFrontS3DeployStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define a S3 bucket that contains a static website
        self.s3_bucket = self._create_hosting_s3_bucket()

        # Creates Cloudfront Origin Access Identity to access a restricted S3
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self,
            'cdkTestOriginAccessIdentity',
        )

        # Allows Origin Access Control to read from S3
        self.s3_bucket.grant_read(origin_access_identity)

        # Define Cloudfront CDN that delivers from S3 bucket
        self.cdn = self._create_cdn(access_identity=origin_access_identity)

    def _create_hosting_s3_bucket(self):
        """ Returns a S3 instance that serves a static website """
        website_bucket = s3.Bucket(
            self,
            'static-website-for-cdkdemo',
            bucket_name = config.WEB_BUCKET_NAME,
            # website_index_document="index.html",
            removal_policy=removalPolicy.DESTROY,
            access_control=s3.BucketAccessControl.PRIVATE,
        )

        # Populates bucket with files from local file system
        s3deploy.BucketDeployment(
            self,
            'DeployWebsite',
            destination_bucket=website_bucket,
            sources=[
                s3deploy.Source.asset(config.WEB_UPLOAD_FOLDER)
            ],
            retain_on_delete=False,
        )
        return website_bucket

    def _create_cdn(self, access_identity):
        """ Returns a CDN that delivers from a S3 bucket """
        return cloudfront.Distribution(
            self,
            'ProteinDataWebsiteDist',
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.s3_bucket,
                    origin_access_identity=access_identity,
                ),
            ),
            domain_names = [config.WEB_DOMAIN_NAME],
            default_root_object=config.WEB_ROOT_FILE,
            certificate = acm.Certificate.from_certificate_arn(self, "domainCert", config.WEB_CERT_ARN)
        )
