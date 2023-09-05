import aws_cdk as cdk
from nyu_protein_website_deploy.config import config
from constructs import Construct
from aws_cdk import (aws_rds as rds,
                     aws_ec2 as ec2,
                     Stack,)

class NyuProteinRDSDeployStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        vpc_id = config.VPC_ID
        if (vpc):
            vpc_id = vpc.vpc_id
            existing_vpc = vpc
        else:
            existing_vpc = ec2.Vpc.from_lookup(self, config.VPC_NAME, vpc_id=vpc_id)
        

        # Create a security group for the RDS cluster
        db_security_group = ec2.SecurityGroup(
            self, f'{config.MYSQL_DB_NAME}-MySQL-SG',
            vpc=existing_vpc,
            description='RDS Security Group',
        )

        db_security_group.add_ingress_rule(
            ec2.Peer.ipv4(config.VPC_CIDR),  # Limit access to specific IP address
            ec2.Port.tcp(3306),
            'Allow MySQL inbound',
        )


        # Password for RDS
        rds_password = cdk.SecretValue.plain_text(config.MYSQL_PASSWORD)

        # Create a serverless Aurora RDS cluster
        cluster = rds.ServerlessCluster(
            self, f'{config.MYSQL_DB_NAME}-cluster',
            engine=rds.DatabaseClusterEngine.AURORA_MYSQL,
            cluster_identifier = config.MYSQL_DB_IDENTIFIER, # Replace with your database name
            vpc=existing_vpc,
            vpc_subnets={
                'subnet_type': ec2.SubnetType.PRIVATE_ISOLATED,
            },
            default_database_name="proteinog",
            security_groups=[db_security_group],
            removal_policy=cdk.RemovalPolicy.DESTROY,  # Change as needed
            credentials = rds.Credentials.from_password(config.MYSQL_USER_NAME, rds_password),
            scaling = rds.ServerlessScalingOptions(
                # auto_pause=Duration.minutes(10),  # default is to pause after 5 minutes of idle time
                min_capacity=rds.AuroraCapacityUnit.ACU_1,  # default is 2 Aurora capacity units (ACUs)
                max_capacity=rds.AuroraCapacityUnit.ACU_32
            )
        )

        cdk.CfnOutput(
            self, 'rdsClusterEndpoint',
            value= cluster.cluster_endpoint.hostname,
        )