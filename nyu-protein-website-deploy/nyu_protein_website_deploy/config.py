class config():

    ACCT_ID = '629244530291'
    ACCT_REGION = 'us-east-1'

    VPC_NAME = 'nyu-vpc'
    VPC_CIDR = '20.0.0.0/16'
    VPC_ID = "vpc-05deee1167bcafa75"
    WEB_LAMBDA_SG = "sg-0bce7780a97cbceab"

    WEB_BUCKET_NAME = "protein1.piyao.com"
    WEB_DOMAIN_NAME = "protein1.piyao.com"
    WEB_ROOT_FILE = "index.html"
    WEB_UPLOAD_FOLDER = "../web"
    WEB_CERT_ARN = "arn:aws:acm:us-east-1:629244530291:certificate/e8b3e1ca-7773-4ff3-b2f1-c1d0feec89da"

    MYSQL_DB_IDENTIFIER = 'nyu-mysql'
    MYSQL_DB_NAME = 'nyuog'
    MYSQL_PASSWORD = '4z(hFH-({u2Y*g:$BL{!D$Rp%H_!'
    MYSQL_RDS_HOST = 'nyu-database.cluster-cnfpwwtkftli.us-east-1.rds.amazonaws.com'
    MYSQL_USER_NAME = 'awsuser'

    NEPTUNE_DB_IDENTIFIER = 'nyu-neptune-2'
    SPARQL_ENDPOINT = 'https://nyu-neptune-instance-1.cnfpwwtkftli.us-east-1.neptune.amazonaws.com:8182/sparql'