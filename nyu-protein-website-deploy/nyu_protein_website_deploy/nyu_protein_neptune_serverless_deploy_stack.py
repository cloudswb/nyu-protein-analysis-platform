import aws_cdk as cdk
from nyu_protein_website_deploy.config import config
from constructs import Construct
from aws_cdk import (aws_neptune_alpha as neptune_alpha,
                     aws_ec2 as ec2,
                     aws_iam as iam,
                     aws_sagemaker as aws_sagemaker,
                     Stack,
                     Tags,
                     Fn)

# from packages.aws_cdk import aws_neptune_alpha as neptune

class NyuProteinNeptuneServerlessDeployStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_id = config.VPC_ID
        if (vpc):
            vpc_id = vpc.vpc_id
            existing_vpc = vpc
        else:
            existing_vpc = ec2.Vpc.from_lookup(self, config.VPC_NAME, vpc_id=vpc_id)

        NEPTUNE_DB_IDENTIFIER = f'{config.NEPTUNE_DB_IDENTIFIER}-SL'
        NEPTUNE_NOTEBOOK_SG = f"{NEPTUNE_DB_IDENTIFIER}-notebook-sg"
        NEPTUNE_SG = f"{NEPTUNE_DB_IDENTIFIER}-sg"
        NEPTUNE_SUBNET_GROUP = f"{NEPTUNE_DB_IDENTIFIER}-subnet-group"
        NEPTUNE_DB_INSTANCE_CLASS =  config.NEPTUNE_DB_INSTANCE_CLASS
        NEPTUNE_NOTEBOOK_INSTANCE_CLASS =  config.NEPTUNE_DB_INSTANCE_CLASS

        
        
        
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
                                                

                                                # associated_roles=[neptuneCluster_role_property],
                                                # db_cluster_identifier=config.NEPTUNE_DB_IDENTIFIER,
                                                # db_subnet_group_name=neptune_Subnet_group.db_subnet_group_name,
                                                
                                                # serverless_scaling_configuration=neptune.CfnDBCluster.ServerlessScalingConfigurationProperty(
                                                #     max_capacity=40,
                                                #     min_capacity=1
                                                # ),
                                                # vpc_security_group_ids=[db_security_group.security_group_id]
                                            )


        

        #####################

        sg_notebook_graph_db = ec2.SecurityGroup(self, NEPTUNE_NOTEBOOK_SG,
        vpc=existing_vpc,
        allow_all_outbound=True,
        description='security group for neptune notebook client',
        security_group_name=NEPTUNE_NOTEBOOK_SG
        )
        Tags.of(sg_notebook_graph_db).add('Name', NEPTUNE_NOTEBOOK_SG)

        sagemaker_notebook_role_policy_doc = iam.PolicyDocument()
        sagemaker_notebook_role_policy_doc.add_statements(iam.PolicyStatement(**{
        "effect": iam.Effect.ALLOW,
        "resources": ["arn:aws:s3:::aws-neptune-notebook",
            "arn:aws:s3:::aws-neptune-notebook/*"],
        "actions": ["s3:GetObject",
            "s3:ListBucket"]
        }))

        sagemaker_notebook_role_policy_doc.add_statements(iam.PolicyStatement(**{
        "effect": iam.Effect.ALLOW,
        "resources": ["arn:aws:neptune-db:{region}:{account}:{cluster_id}/*".format(
            region=config.ACCT_REGION, account=config.ACCT_ID, cluster_id=graph_db.cluster_resource_identifier)],
        "actions": ["neptune-db:connect"]
        }))

        sagemaker_notebook_role = iam.Role(self, f'{NEPTUNE_DB_IDENTIFIER}-Notebook-ForNeptuneWorkbenchRole',
        role_name=f'AWSNeptuneNotebookRole-{NEPTUNE_DB_IDENTIFIER}-NeptuneNotebook',
        assumed_by=iam.ServicePrincipal('rds.amazonaws.com'),
        #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
        inline_policies={
            'AWSNeptuneNotebook': sagemaker_notebook_role_policy_doc
        }
        )

        sagemaker_notebook_role.add_managed_policy(iam.ManagedPolicy.from_managed_policy_name(self,f'{NEPTUNE_DB_IDENTIFIER}-POLICY-AmazonS3FullAccess','AmazonS3FullAccess'))


        neptune_wb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'

echo "export GRAPH_NOTEBOOK_AUTH_MODE=DEFAULT" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_HOST={NeptuneClusterEndpoint}" >> ~/.bashrc
echo "export GRAPH_NOTEBOOK_PORT={NeptuneClusterPort}" >> ~/.bashrc
echo "export NEPTUNE_LOAD_FROM_S3_ROLE_ARN=''" >> ~/.bashrc
echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc

aws s3 cp s3://aws-neptune-notebook/graph_notebook.tar.gz /tmp/graph_notebook.tar.gz
rm -rf /tmp/graph_notebook
tar -zxvf /tmp/graph_notebook.tar.gz -C /tmp
chmod +x /tmp/graph_notebook/install.shy
/tmp/graph_notebook/install.sh

cd /tmp/
git clone https://github.com/cloudswb/nyu-protein-analysis-platform.git
mkdir -p ~/SageMaker/ProteinDC
cp -r /tmp/nyu-protein-analysis-platform/nyu-protein-website-deploy/nyu_protein_website_deploy/notebook ~/SageMaker/ProteinDC

EOF
'''.format(NeptuneClusterEndpoint=graph_db.cluster_endpoint.hostname,
    NeptuneClusterPort=graph_db.cluster_endpoint.port,
    AWS_Region=config.ACCT_REGION)


        neptune_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
            content=Fn.base64(neptune_wb_lifecycle_content)
        )

        neptune_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, f'{NEPTUNE_DB_IDENTIFIER}NpetuneWorkbenchLifeCycleConfig',
        notebook_instance_lifecycle_config_name='ProteinDCNeptuneWorkbenchLifeCycleConfig',
        on_start=[neptune_wb_lifecycle_config_prop]
        )

        neptune_workbench = aws_sagemaker.CfnNotebookInstance(self, f'{NEPTUNE_DB_IDENTIFIER}NeptuneWorkbench',
            instance_type=config.NEPTUNE_NOTEBOOK_INSTANCE_CLASS,
            role_arn=sagemaker_notebook_role.role_arn,
            lifecycle_config_name=neptune_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
            notebook_instance_name=f'{NEPTUNE_DB_IDENTIFIER}NeptuneTutorialWorkbench',
            root_access='Disabled',
            security_group_ids=[sg_notebook_graph_db.security_group_id],
            # subnet_id=graph_db.vpc_subnets.subnets.pop(0).subnet_id
        )


        ######################


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
            self, 'neptuneNotebookInstanceName',
            value= neptune_workbench.notebook_instance_name
        )

        cdk.CfnOutput(
            self, 'neptuneLoadS3Role',
            value= neptune_load_s3_role.role_arn
        )
        