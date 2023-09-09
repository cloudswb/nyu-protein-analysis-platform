import aws_cdk as cdk
import time
from deploy.config import config

from constructs import Construct
from aws_cdk import (aws_ec2 as ec2,
                     Stack,)

class ProteinDCVpcDeployStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # self.vpc_name = 'vpc-demo'
        # self.vpc_cidr = '20.0.0.0/16'

        # vpc_construct_id = 'NYU-VPC'

        # audit_bucket_construct_id = 'audit-bucket'
        # audit_bucket_name = config.WEB_BUCKET_NAME
        # self.audit_bucket = s3.Bucket.from_bucket_name(
        #     self, audit_bucket_construct_id, audit_bucket_name
        # )

        vpc = ec2.Vpc(self, config.VPC_NAME,
            ip_addresses=ec2.IpAddresses.cidr(config.VPC_CIDR),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name='Public',
                    cidr_mask=20
                ), ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name='Compute',
                    cidr_mask=20
                ), ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    name='RDS',
                    cidr_mask=20
                )
            ],
            nat_gateways=1,
        )

        # Alternatively gateway endpoints can be added on the VPC
        s3_endpoint = vpc.add_gateway_endpoint("S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )

        self.vpc = vpc
        # config.VPC_ID = vpc.vpc_id

        time.sleep(30)

        cdk.CfnOutput(
            self, 'VPC ID',
            value=vpc.vpc_id,
        )

