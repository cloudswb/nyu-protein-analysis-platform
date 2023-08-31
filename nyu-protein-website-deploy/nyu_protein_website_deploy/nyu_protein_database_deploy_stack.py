import aws_cdk as cdk
from nyu_protein_website_deploy.config import Config
from constructs import Construct
from aws_cdk import (aws_apigateway as apigateway,
                     aws_s3 as s3,
                     aws_neptune as neptune,
                     aws_rds as rds,
                     aws_ec2 as ec2,
                     Stack,)

class NyuProteinDatabaseDeployStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        existing_vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_id = Config.VPC_ID)

        # Define Neptune cluster
        neptune_cluster = neptune.DatabaseCluster(self, "ServerlessDatabase",
                                    vpc = existing_vpc,
                                    instance_type = neptune.InstanceType.SERVERLESS,
                                    serverless_scaling_configuration=neptune.ServerlessScalingConfiguration(
                                        min_capacity=1,
                                        max_capacity=5
                                    ))
        
        
        # neptune.DatabaseCluster(self, "NeptuneCluster",
        #     vpc=existing_vpc,
        #     instance_type = neptune.InstanceType.SERVERLESS,
            
        #     # instanceType: InstanceType.SERVERLESS,
        #     # clusterParameterGroup,
        #     # removalPolicy: cdk.RemovalPolicy.DESTROY,
        #     # serverlessScalingConfiguration: {
        #     #     minCapacity: 1,
        #     #     maxCapacity: 5,
        #     # },
        #     removal_policy=core.RemovalPolicy.DESTROY  # For demo purposes; consider other policies
        # )

        # Define Aurora MySQL database instance
        aurora_mysql = rds.DatabaseCluster(self, "Database",
                                            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_08_1),
                                            writer=rds.ClusterInstance.provisioned("writer",
                                                instance_type=ec2.InstanceType.of(ec2.InstanceClass.R6G, ec2.InstanceSize.XLARGE4)
                                            ),
                                            serverless_v2_min_capacity = 0.5,
                                            serverless_v2_max_capacity = 10,
                                            readers =[
                                                # will be put in promotion tier 1 and will scale with the writer
                                                rds.ClusterInstance.serverless_v2("reader1", scale_with_writer=True),
                                                # will be put in promotion tier 2 and will not scale with the writer
                                                rds.ClusterInstance.serverless_v2("reader2")
                                            ],
                                            vpc = existing_vpc
                                        )
                                                
        
        # rds.DatabaseInstance(self, "AuroraMySQL",
        #     engine = rds.DatabaseInstanceEngine.AURORA_MYSQL,
        #     instance_type= rds.
        #     vpc=existing_vpc,
        #     removal_policy=core.RemovalPolicy.DESTROY,  # For demo purposes; consider other policies
        #     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),  # Use private subnets
        #     security_groups=[neptune_cluster.connections.security_groups[0]]  # Allow Neptune traffic
        # )