# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
  Fn,
  aws_ec2,
  aws_s3 as s3,
  aws_neptune,
  aws_iam,
  aws_sagemaker,
  Stack,
  Tags
)
from nyu_protein_website_deploy.config import config


class NyuProteinNeptuneDeployStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc: aws_ec2.Vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)


    vpc_id = config.VPC_ID
    if (vpc):
        vpc_id = vpc.vpc_id
        existing_vpc = vpc
    else:
        existing_vpc = aws_ec2.Vpc.from_lookup(self, config.VPC_NAME, vpc_id=vpc_id)

    NEPTUNE_DB_IDENTIFIER = config.NEPTUNE_DB_IDENTIFIER
    NEPTUNE_NOTEBOOK_SG = f"{NEPTUNE_DB_IDENTIFIER}-notebook-sg"
    NEPTUNE_SG = f"{NEPTUNE_DB_IDENTIFIER}-sg"
    NEPTUNE_SUBNET_GROUP = f"{NEPTUNE_DB_IDENTIFIER}-subnet-group"
    NEPTUNE_DB_INSTANCE_CLASS =  config.NEPTUNE_DB_INSTANCE_CLASS


    sg_notebook_graph_db = aws_ec2.SecurityGroup(self, NEPTUNE_NOTEBOOK_SG,
      vpc=existing_vpc,
      allow_all_outbound=True,
      description='security group for neptune notebook client',
      security_group_name=NEPTUNE_NOTEBOOK_SG,
    )
    Tags.of(sg_notebook_graph_db).add('Name', NEPTUNE_NOTEBOOK_SG,)

    sg_graph_db = aws_ec2.SecurityGroup(self, NEPTUNE_SG,
      vpc=existing_vpc,
      allow_all_outbound=True,
      description='security group for neptune db',
      security_group_name=NEPTUNE_SG,
    )
    Tags.of(sg_graph_db).add('Name', NEPTUNE_SG)

    sg_graph_db.add_ingress_rule(peer=sg_graph_db, connection=aws_ec2.Port.tcp(8182), description=NEPTUNE_SG)
    sg_graph_db.add_ingress_rule(peer=sg_notebook_graph_db, connection=aws_ec2.Port.tcp(8182), description=NEPTUNE_NOTEBOOK_SG)

    graph_db_subnet_group = aws_neptune.CfnDBSubnetGroup(self, NEPTUNE_SUBNET_GROUP,
      db_subnet_group_description='subnet group for ProteinDC neptune db',
      subnet_ids=existing_vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED).subnet_ids,
      db_subnet_group_name=NEPTUNE_SUBNET_GROUP
    )

      # Create an IAM role for Neptune
    neptune_load_s3_role = aws_iam.Role(
        self, f'{NEPTUNE_DB_IDENTIFIER}-ACCESS-S3-Role',
        assumed_by=aws_iam.ServicePrincipal('rds.amazonaws.com'),
        description='IAM role for Neptune to access S3',
        managed_policies=[
            aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess'),  # Adjust permissions as needed
        ],
    )

    graph_db = aws_neptune.CfnDBCluster(self, f'{NEPTUNE_DB_IDENTIFIER}-Cluster',
                                        associated_roles=[aws_neptune.CfnDBCluster.DBClusterRoleProperty(
                                                            role_arn=neptune_load_s3_role.role_arn,
                                                            feature_name="featureName"
                                                        )],
                                        availability_zones=existing_vpc.availability_zones,
                                        db_subnet_group_name=graph_db_subnet_group.db_subnet_group_name,
                                        db_cluster_identifier=f'{NEPTUNE_DB_IDENTIFIER}-Cluster',
                                        backup_retention_period=1,
                                        preferred_backup_window='22:45-23:15',
                                        preferred_maintenance_window='sun:18:00-sun:18:30',
                                        vpc_security_group_ids=[sg_graph_db.security_group_id],
                                      )
    graph_db.add_depends_on(graph_db_subnet_group)

    
    graph_db_instance = aws_neptune.CfnDBInstance(self, f'{NEPTUNE_DB_IDENTIFIER}-Instance',
      db_instance_class=NEPTUNE_DB_INSTANCE_CLASS,
      allow_major_version_upgrade=False,
      auto_minor_version_upgrade=False,
      availability_zone=existing_vpc.availability_zones[0],
      db_cluster_identifier=graph_db.db_cluster_identifier,
      db_instance_identifier=f'{NEPTUNE_DB_IDENTIFIER}-Instance',
      preferred_maintenance_window='sun:18:00-sun:18:30',
    )
    graph_db_instance.add_depends_on(graph_db)

    # graph_db_replica_instance = aws_neptune.CfnDBInstance(self, 'NeptuneTutorialReplicaInstance',
    #   db_instance_class='db.r5.large',
    #   allow_major_version_upgrade=False,
    #   auto_minor_version_upgrade=False,
    #   availability_zone=vpc.availability_zones[-1],
    #   db_cluster_identifier=graph_db.db_cluster_identifier,
    #   db_instance_identifier='neptune-tutorial-replica',
    #   preferred_maintenance_window='sun:18:00-sun:18:30'
    # )
    # graph_db_replica_instance.add_depends_on(graph_db)
    # graph_db_replica_instance.add_depends_on(graph_db_instance)

    sagemaker_notebook_role_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::aws-neptune-notebook",
        "arn:aws:s3:::aws-neptune-notebook/*"],
      "actions": ["s3:GetObject",
        "s3:ListBucket"]
    }))

    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:neptune-db:{region}:{account}:{cluster_id}/*".format(
        region=config.ACCT_REGION, account=config.ACCT_ID, cluster_id=graph_db.attr_cluster_resource_id)],
      "actions": ["neptune-db:connect"]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, f'{NEPTUNE_DB_IDENTIFIER}-Notebook-ForNeptuneWorkbenchRole',
      role_name=f'AWSNeptuneNotebookRole-{NEPTUNE_DB_IDENTIFIER}-NeptuneNotebook',
      assumed_by=aws_iam.ServicePrincipal('rds.amazonaws.com'),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        'AWSNeptuneNotebook': sagemaker_notebook_role_policy_doc
      }
    )

    sagemaker_notebook_role.add_managed_policy(aws_iam.ManagedPolicy.from_managed_policy_name(self, f'{NEPTUNE_DB_IDENTIFIER}-POLICY-AmazonS3FullAccess', 'AmazonS3ReadOnlyAccess'))


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
'''.format(NeptuneClusterEndpoint=graph_db.attr_endpoint,
    NeptuneClusterPort=graph_db.attr_port,
    AWS_Region=config.ACCT_REGION)


    neptune_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=Fn.base64(neptune_wb_lifecycle_content)
    )

    neptune_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, f'{NEPTUNE_DB_IDENTIFIER}NpetuneWorkbenchLifeCycleConfig',
      notebook_instance_lifecycle_config_name=f'{NEPTUNE_DB_IDENTIFIER}NeptuneWorkbenchLifeCycleConfig',
      on_start=[neptune_wb_lifecycle_config_prop]
    )

    neptune_workbench = aws_sagemaker.CfnNotebookInstance(self, f'{NEPTUNE_DB_IDENTIFIER}NeptuneWorkbench',
      instance_type=config.NEPTUNE_NOTEBOOK_INSTANCE_CLASS,
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=neptune_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name=f'{NEPTUNE_DB_IDENTIFIER}NeptuneNotebookWorkbench',
      root_access='Disabled',
      security_group_ids=[sg_notebook_graph_db.security_group_id],
      subnet_id=graph_db_subnet_group.subnet_ids[0]
    )




    # Output the  instance endpoint
    cdk.CfnOutput(
        self, 'neptuneClusterEndpoint',
        value= graph_db.attr_endpoint,
    )

    cdk.CfnOutput(
        self, 'neptuneClusterPort',
        value= f'{graph_db.attr_port}',
    )

    cdk.CfnOutput(
        self, 'neptuneNotebookInstanceName',
        value= neptune_workbench.notebook_instance_name
    )

    cdk.CfnOutput(
        self, 'neptuneLoadS3Role',
        value=neptune_load_s3_role.role_arn
    )
    