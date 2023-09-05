class config():

    ACCT_ID = ''
    ACCT_REGION = 'us-east-1'

    VPC_NAME = 'nyu-vpc'
    VPC_CIDR = '20.0.0.0/16'
    VPC_ID = "vpc-05deee1167bcafa75"
    IS_NEPTUNE_SERVERLESS = True

    WEB_BUCKET_NAME = "proteinxxx.xxx.com"
    WEB_DOMAIN_NAME = "proteinxx.xxx.com"
    WEB_ROOT_FILE = "index.html"
    WEB_UPLOAD_FOLDER = "../web"
    WEB_CERT_ARN = "arn:aws:acm:us-east-1:629244530291:certificate/e8b3e1ca-7773-4ff3-b2f1-c1d0feec89da"

    MYSQL_DB_IDENTIFIER = 'nyu-mysql'
    MYSQL_DEFAULT_DB_NAME = 'proteinog'
    MYSQL_PASSWORD = '4z(hFH-({u2Y*g:$BL{!D$Rp%H_!'
    MYSQL_USER_NAME = 'awsuser'

    NEPTUNE_DB_IDENTIFIER = 'proteindc-neptune'
    NEPTUNE_DB_INSTANCE_CLASS = 'db.r6g.4xlarge'
    NEPTUNE_NOTEBOOK_INSTANCE_CLASS = 'ml.t3.large'