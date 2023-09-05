class config():

    # 标注【必须修改】的信息是必须根据自己的情况修改，其他信息可以视情况修改

    ACCT_ID = '' #部署的账号ID【必须修改】
    ACCT_REGION = 'us-east-1' #部署到的区域代码，默认为美东

    VPC_NAME = 'nyu-vpc' #新建VPC的名称
    VPC_CIDR = '20.0.0.0/16' #新建VPC的IP网段
    

    WEB_BUCKET_NAME = "proteinxxx.xxx.com" #存储前端网页代码的存储桶名称 【必须修改】
    WEB_DOMAIN_NAME = "proteinxx.xxx.com" #部署的自有域名 【必须修改】
    WEB_ROOT_FILE = "index.html" #网站默认页面
    WEB_UPLOAD_FOLDER = "../web" #网站在git代码中的位置
    WEB_CERT_ARN = "arn:aws:acm:xxxx" #网站使用的SSL证书ARN信息 【必须修改】

    MYSQL_DB_IDENTIFIER = 'nyu-mysql' #用于存储网络结构的RDS MySQL数据库的实例名称
    MYSQL_DEFAULT_DB_NAME = 'proteinog' #RDS数据库实例的默认数据库
    MYSQL_PASSWORD = '4z(hFH-({u2Y*g:$BL{!D$Rp%H_!' #RDS数据库实例的密码
    MYSQL_USER_NAME = 'awsuser' #RDS数据库的用户吗

    IS_NEPTUNE_SERVERLESS = True # 是否部署无服务化的Neptune数据库
    NEPTUNE_DB_IDENTIFIER = 'proteindc-neptune' #图形数据库的实例名称
    NEPTUNE_DB_INSTANCE_CLASS = 'db.r6g.4xlarge' #图数据库的实例类型（如果IS_NEPTUNE_SERVERLESS为True，则不需要该值）

    NEPTUNE_NOTEBOOK_INSTANCE_CLASS = 'ml.t3.large' #Notebook实例的类型