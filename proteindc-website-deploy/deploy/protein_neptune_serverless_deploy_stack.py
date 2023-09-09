import aws_cdk as cdk
from deploy.config import config
from constructs import Construct
from aws_cdk import (aws_neptune_alpha as neptune_alpha,
                     aws_ec2 as ec2,
                     aws_iam as iam,
                     aws_sagemaker as aws_sagemaker,
                     Stack,
                     Tags,
                     Fn)

class ProteinDCNeptuneServerlessDeployStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        existing_vpc = vpc

        NEPTUNE_DB_IDENTIFIER = f'{config.NEPTUNE_DB_IDENTIFIER}-serverless'
        NEPTUNE_NOTEBOOK_SG = f"{NEPTUNE_DB_IDENTIFIER}-notebook-sg"
        NEPTUNE_SG = f"{NEPTUNE_DB_IDENTIFIER}-sg"
        NEPTUNE_SUBNET_GROUP = f"{NEPTUNE_DB_IDENTIFIER}-subnet-group"
        # NEPTUNE_DB_INSTANCE_CLASS =  config.NEPTUNE_DB_INSTANCE_CLASS
        # NEPTUNE_NOTEBOOK_INSTANCE_CLASS =  config.NEPTUNE_DB_INSTANCE_CLASS

        
        # Create a security group for the RDS cluster
        db_security_group = ec2.SecurityGroup(
            self, NEPTUNE_SG,
            vpc=existing_vpc,
            description='Neptune Security Group',
        )

        db_security_group.add_ingress_rule(
            ec2.Peer.ipv4(config.VPC_CIDR),  # Limit access to specific IP address
            ec2.Port.tcp(8182),
            'Allow MySQL inbound',
        )


        # neptune_Subnet_group = neptune.CfnDBSubnetGroup(self, "MyCfnDBSubnetGroup",
        #     db_subnet_group_description="dbSubnetGroupDescription",
        #     subnet_ids=existing_vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED).subnet_ids,
        #     # the properties below are optional
        #     db_subnet_group_name="nyu-neptune-sg",
        #     # tags=[cdk.CfnTag(
        #     #     key="key",
        #     #     value="value"
        #     # )]
        # )

        subnet_group = neptune_alpha.SubnetGroup(self, NEPTUNE_SUBNET_GROUP,
            vpc=existing_vpc,

            # the properties below are optional
            description="Neptune Subnet Group",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            subnet_group_name=NEPTUNE_SUBNET_GROUP,
            # vpc_subnets=existing_vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED).subnet_ids,
            vpc_subnets = ec2.SubnetSelection(
                                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
                            )
        )


         # Create an IAM role for Neptune
        neptune_load_s3_role = iam.Role(
            self, f'{NEPTUNE_DB_IDENTIFIER}-ACCESS-S3-Role',
            assumed_by=iam.ServicePrincipal('rds.amazonaws.com'),
            description='IAM role for Neptune to access S3',
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess'),  # Adjust permissions as needed
            ],
        )


        graph_db = neptune_alpha.DatabaseCluster(self, f"{NEPTUNE_DB_IDENTIFIER}-Cluster",
                                                associated_roles = [neptune_load_s3_role],
                                                vpc = existing_vpc,
                                                instance_type=neptune_alpha.InstanceType.SERVERLESS,
                                                serverless_scaling_configuration=neptune_alpha.ServerlessScalingConfiguration(
                                                    min_capacity=1,
                                                    max_capacity=40,
                                                ),
                                                security_groups = [db_security_group],
                                                subnet_group = subnet_group,
                                                db_cluster_name = f'{NEPTUNE_DB_IDENTIFIER}-Cluster',
                                                instance_identifier_base=f'{NEPTUNE_DB_IDENTIFIER}',

                                                # associated_roles=[neptuneCluster_role_property],
                                                # db_cluster_identifier=config.NEPTUNE_DB_IDENTIFIER,
                                                # db_subnet_group_name=neptune_Subnet_group.db_subnet_group_name,
                                                
                                                # serverless_scaling_configuration=neptune.CfnDBCluster.ServerlessScalingConfigurationProperty(
                                                #     max_capacity=40,
                                                #     min_capacity=1
                                                # ),
                                                # vpc_security_group_ids=[db_security_group.security_group_id]
                                            )

        self.graph_db_ep = graph_db.cluster_endpoint.hostname
        self.graph_db_ep_port = graph_db.cluster_endpoint.port
        self.graph_db_attr_cluster_resource_id = graph_db.cluster_resource_identifier

        # Output the  instance endpoint
        cdk.CfnOutput(
            self, 'neptuneClusterEndpoint',
            value= graph_db.cluster_endpoint.hostname,
        )

        cdk.CfnOutput(
            self, 'neptuneClusterPort',
            value= f'{graph_db.cluster_endpoint.port}',
        )

        cdk.CfnOutput(
            self, 'neptuneLoadS3Role',
            value= f'{neptune_load_s3_role.role_arn}',
        )
