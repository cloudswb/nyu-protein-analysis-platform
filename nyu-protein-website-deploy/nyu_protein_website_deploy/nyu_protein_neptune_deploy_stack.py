# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
from constructs import Construct
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

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)



    # The code that defines your stack goes here
#     vpc = aws_ec2.Vpc(self, "NeptuneTutorialVPC",
#       max_azs=2,
# #      subnet_configuration=[{
# #          "cidrMask": 24,
# #          "name": "Public",
# #          "subnetType": aws_ec2.SubnetType.PUBLIC,
# #        },
# #        {
# #          "cidrMask": 24,
# #          "name": "Private",
# #          "subnetType": aws_ec2.SubnetType.PRIVATE
# #        },
# #        {
# #          "cidrMask": 28,
# #          "name": "Isolated",
# #          "subnetType": aws_ec2.SubnetType.ISOLATED,
# #          "reserved": True
# #        }
# #      ],
#       gateway_endpoints={
#         "S3": aws_ec2.GatewayVpcEndpointOptions(
#           service=aws_ec2.GatewayVpcEndpointAwsService.S3
#         )
#       }
#     )


    vpc_id = "vpc-05deee1167bcafa75"
    vpc = aws_ec2.Vpc.from_lookup(self, config.VPC_NAME, vpc_id=vpc_id)

    sg_notebook_graph_db = aws_ec2.SecurityGroup(self, "ProteinDCNeptuneNotebookSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune notebook client',
      security_group_name='proteindc-neptune-notebook-sg'
    )
    Tags.of(sg_notebook_graph_db).add('Name', 'proteindc-neptune-notebook-sg')

    sg_graph_db = aws_ec2.SecurityGroup(self, "ProteinDCNeptuneSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for neptune db',
      security_group_name='proteindc-neptune-db-sg'
    )
    Tags.of(sg_graph_db).add('Name', 'proteindc-neptune-db-sg')

    sg_graph_db.add_ingress_rule(peer=sg_graph_db, connection=aws_ec2.Port.tcp(8182), description='proteindc-neptune-db-sg')
    sg_graph_db.add_ingress_rule(peer=sg_notebook_graph_db, connection=aws_ec2.Port.tcp(8182), description='proteindc-neptune-notebook-sg')

    graph_db_subnet_group = aws_neptune.CfnDBSubnetGroup(self, 'ProteinDCNeptuneDBSubnetGroup',
      db_subnet_group_description='subnet group for ProteinDC neptune db',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED).subnet_ids,
      db_subnet_group_name='proteindc-neptune-db-sg'
    )

    graph_db = aws_neptune.CfnDBCluster(self, 'ProteinDCNeptuneDB',
      availability_zones=vpc.availability_zones,
      db_subnet_group_name=graph_db_subnet_group.db_subnet_group_name,
      db_cluster_identifier='proteindc-neptune-db-cluster',
      backup_retention_period=1,
      preferred_backup_window='22:45-23:15',
      preferred_maintenance_window='sun:18:00-sun:18:30',
      vpc_security_group_ids=[sg_graph_db.security_group_id]
    )
    graph_db.add_depends_on(graph_db_subnet_group)

    graph_db_instance = aws_neptune.CfnDBInstance(self, 'NeptuneTutorialInstance',
      db_instance_class='db.r6g.4xlarge',
      allow_major_version_upgrade=False,
      auto_minor_version_upgrade=False,
      availability_zone=vpc.availability_zones[0],
      db_cluster_identifier=graph_db.db_cluster_identifier,
      db_instance_identifier='proteindc-neptune-db-instance',
      preferred_maintenance_window='sun:18:00-sun:18:30'
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

    sagemaker_notebook_role = aws_iam.Role(self, 'ProteinDCSageMakerNotebookForNeptuneWorkbenchRole',
      role_name='AWSNeptuneNotebookRole-ProteinDCNeptuneNotebook',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        'AWSNeptuneNotebook': sagemaker_notebook_role_policy_doc
      }
    )

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
      /tmp/graph_notebook/install.sh

      cd /tmp/
      git clone https://github.com/cloudswb/nyu-protein-analysis-platform.git

      mkdir -p ~/SageMaker/ProteinDC
      cp /tmp/nyu-protein-analysis-platform/nyu-protein-website-deploy/nyu_protein_website_deploy/notebook ~/SageMaker/ProteinDC

      EOF
      '''.format(NeptuneClusterEndpoint=graph_db.attr_endpoint,
          NeptuneClusterPort=graph_db.attr_port,
          AWS_Region=config.ACCT_REGION)

    neptune_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=Fn.base64(neptune_wb_lifecycle_content)
    )

    neptune_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'ProteinDCNpetuneWorkbenchLifeCycleConfig',
      notebook_instance_lifecycle_config_name='ProteinDCNeptuneWorkbenchLifeCycleConfig',
      on_start=[neptune_wb_lifecycle_config_prop]
    )

    neptune_workbench = aws_sagemaker.CfnNotebookInstance(self, 'ProteinDCNeptuneWorkbench',
      instance_type='ml.t3.large',
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=neptune_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name='ProteinDCNeptuneTutorialWorkbench',
      root_access='Disabled',
      security_group_ids=[sg_notebook_graph_db.security_group_id],
      subnet_id=graph_db_subnet_group.subnet_ids[0]
    )

