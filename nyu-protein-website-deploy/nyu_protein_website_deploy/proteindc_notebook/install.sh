#!/bin/bash
cd ~
git clone https://github.com/cloudswb/nyu-protein-analysis-platform.git

mkdir -p ~/SageMaker/ProteinDC
cp ~/nyu-protein-analysis-platform/nyu-protein-website-deploy/nyu_protein_website_deploy/notebook ~/SageMaker/ProteinDC

echo "done."