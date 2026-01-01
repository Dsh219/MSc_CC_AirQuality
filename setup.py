# -*- coding: utf-8 -*-
print(">>>>> Starting setup <<<<<")
import boto3
from botocore.config import Config
import zipfile
import json
stage = 1
total_stages = 8
#---------------------------------------------------------------------------------#
## Load credentials and define vars
print(f">>>>> {stage}/{total_stages} Loading AWS credentials and vars...")
#with open('./credentials/credentials.txt', 'r') as file:
with open('../credentials.txt', 'r') as file:
    lines = file.readlines()
    access_key = lines[1].split("=")[1].strip()
    secret_key = lines[2].split("=")[1].strip()
    token = lines[3].split("=")[1].strip()
region = 'us-east-1'

# Define vars for setup
python_version = 'python3.12'         # specify the Python version for Lambda functions pyarrow layer compatibility
S3_bucket_data = 'cloudcomputing-20251222'   # has to be globally unique
S3_bucket_frontend = 'cloud-computing-frontend-20251222'  # has to be globally unique
EC2_security_group_name = 'cloud-computing-CC'
dynamodb_name = 'DailyAQI'
role_name = "LabRole"
hourly_rule_name = "lambda_hourly_trigger"
s3_web_endpoint = "s3-website-us-east-1.amazonaws.com" # for US East (N. Virginia) region, details at https://docs.aws.amazon.com/general/latest/gr/s3.html#s3_website_region_endpoints
                                                        
print("AWS credentials and vars loaded <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#
## Create a session
print(f">>>>> {stage}/{total_stages} Creating AWS session...")
session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    aws_session_token=token,
    region_name=region
)
print("AWS session created <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#
## Get IAM role ARN
print(f">>>>> {stage}/{total_stages} Retrieving IAM role {role_name}...")
iamC = session.client('iam')
try:
    response = iamC.get_role(RoleName=role_name)
    role_arn = response['Role']['Arn']
except Exception as e:
    raise Exception(f"Setup stopped! => Failed to retrieve IAM role {role_name} : {e}")
print(f"IAM role {role_name} with ARN <{role_arn}> found <<<<< done")
stage += 1
#'''
#---------------------------------------------------------------------------------#
## S3 setup
print(f">>>>> {stage}/{total_stages} Creating S3 buckets")
s3C = session.client('s3')

#******************Frontend S3 bucket creation below*******************************#
print(f"Creating S3 bucket for frontend with name= {S3_bucket_frontend} ...")
try:
    s3C.create_bucket(Bucket=S3_bucket_frontend)
    s3C.put_public_access_block(
        Bucket=S3_bucket_frontend,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': False,
            'IgnorePublicAcls': False,
            'BlockPublicPolicy': False,
            'RestrictPublicBuckets': False
        } 
    )
    # policy is copied from S3 tutorial https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteAccessPermissionsReqd.html#bucket-policy-static-site
    website_policy = {
                        "Version": "2012-10-17",		 	 	 
                        "Statement": [
                            {
                                "Sid": "PublicReadGetObject",
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": [
                                    "s3:GetObject"
                                ],
                                "Resource": [
                                    f"arn:aws:s3:::{S3_bucket_frontend}/*"
                                ]
                            }
                        ]
                    }
    # assign the policy to the bucket
    s3C.put_bucket_policy(
        Bucket=S3_bucket_frontend,
        Policy=json.dumps(website_policy)
    )
    # make the bucket a website
    s3C.put_bucket_website(
        Bucket=S3_bucket_frontend,
        WebsiteConfiguration={
            'IndexDocument': {'Suffix': 'index.html'}
        }
    )
    website_url = f"http://{S3_bucket_frontend}.{s3_web_endpoint}"
except Exception as e:
    raise Exception(f"Setup stopped! => Failed to create S3 bucket with name= {S3_bucket_frontend} : {e}")
print(f"S3 bucket for frontend with name= {S3_bucket_frontend} has been created successfully with public access... <<done")
#******************Frontend S3 bucket creation above******************************#

#******************Data S3 bucket creation below**********************************#
print(f"Creating S3 bucket for data with name= {S3_bucket_data} ...")
try:
    s3C.create_bucket(Bucket=S3_bucket_data) 
    s3C.put_bucket_cors(
        Bucket=S3_bucket_data,
        CORSConfiguration={
            'CORSRules': [  
                    {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET'],
                    'AllowedOrigins': [website_url],
                    'MaxAgeSeconds': 3000
                    }
                ]
            }
        )
except Exception as e:
    raise Exception(f"Setup stopped! => Failed to create S3 bucket with name= {S3_bucket_data} : {e}")
print(f"S3 bucket for data with name= {S3_bucket_data} has been created successfully with traffic restrictions only from frontend... <<done")
#******************Data S3 bucket creation above***********************************#

print(f"S3 buckets have been created successfully... <<<<< done")
stage += 1

#---------------------------------------------------------------------------------#
# EC2 security group setup
print(f">>>>> {stage}/{total_stages} Creating EC2 security group with name= {EC2_security_group_name}")
config = Config(
        retries = {
            'max_attempts': 5,
            'mode': 'standard'
        }
    )
ec2C = session.client('ec2',config=config)
response = ec2C.create_security_group(
    GroupName=EC2_security_group_name,
    Description='Security group for cloud-computing CC'
)
sg_id = response['GroupId']
# setting inbound rules
print(f"Setting inbound rules for security group - {EC2_security_group_name} with id= {sg_id} ...")
ec2C.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 0,
            'ToPort': 65535,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allows all IPv4
        }
    ]
)
print(f"Security group - {EC2_security_group_name} have been set... <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#
## DynamoDB setup
print(f">>>>> {stage}/{total_stages} Creating DynamoDB table with name= {dynamodb_name}")
dynamodbC = session.client('dynamodb')
table = dynamodbC.create_table(
    TableName=dynamodb_name,
    KeySchema=[
        {
            'AttributeName': 'geo',
            'KeyType': 'HASH'  # Partition key
        },
        {
            'AttributeName': 'timestamp',
            'KeyType': 'RANGE'  # Sort key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'geo',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'timestamp',
            'AttributeType': 'S'
        }, # GSI attributes below
        {
            'AttributeName': 'location',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'id',
            'AttributeType': 'S'
        }

    ],
    GlobalSecondaryIndexes=[
        {   
            'IndexName': 'dailyindex',
            'KeySchema': [
                {
                    'AttributeName': 'location',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'id',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            }
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)
# Wait until the table exists
waiter = dynamodbC.get_waiter('table_exists')
waiter.wait(TableName=dynamodb_name)
print(f"{dynamodb_name} has been created successfully...")
# Enable TTL on the table
dynamodbC.update_time_to_live(
    TableName=dynamodb_name,
    TimeToLiveSpecification={
        'Enabled': True,
        'AttributeName': 'expires_at'
    }   
)
print(f"{dynamodb_name} has been assigned TTL...")
print(f"Creating DynamoDB table with name= {dynamodb_name} <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#
#''' 
## Lambda setup
print(f">>>>> {stage}/{total_stages} Creating Lambda functions...")
lambdaC = session.client('lambda')
# Define Lambda functions and their zip file paths
lambdas = {
    'lambda_hourly': {
        'zip': './zips/lambda_hourly.zip',
        'file': 'lambda_hourly.py' 
    },
    'lambda_daily': {
        'zip': './zips/lambda_daily.zip',
        'file': 'lambda_daily.py'
    },
    'pyarrow-layer': {
        'zip': './zips/daily-layer.zip' # Lambda layer for pyarrow, has to be compressed by a Linux system
    }
}
#******************Hourly lambda creation below************************************#
# Create zip files for Lambda functions
print("Creating zip files for Hourly Lambda function to ./zips ...")
#-Hourly function
with zipfile.ZipFile(lambdas['lambda_hourly']['zip'], 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(lambdas['lambda_hourly']['file'], arcname=lambdas['lambda_hourly']['file'])

print("Zip files for Lambda functions have been created << done")
# Create Lambda functions
print("Creating Lambda functions ...")
    #-Hourly function
with open(lambdas['lambda_hourly']['zip'], 'rb') as f:
    zipped_code = f.read()

response = lambdaC.create_function(
    FunctionName='lambda_hourly',
    Runtime=python_version,
    Role=role_arn,
    Handler='lambda_hourly.lambda_handler',
    Code={
        'ZipFile': zipped_code
    },
    Environment={
        'Variables': {
            'DYNAMODB_TABLE': dynamodb_name
        }
    },
    Timeout=60*2, # 2 minutes > 
    Description='Fetches hourly air quality data and stores in DynamoDB'
)
hourlyF_arn = response['FunctionArn'] # hourly Lambda function ARN
print("Creating Daily Lambda function << done")
#******************Hourly lambda creation above************************************#

#******************Daily lambda creation below*************************************#
# Create Lambda layer for pyarrow
print("Creating Lambda layer for pyarrow...")
with open(lambdas['pyarrow-layer']['zip'], 'rb') as f:
    zipped_code = f.read()
response = lambdaC.publish_layer_version(
    LayerName='pyarrow-layer',
    CompatibleRuntimes=[python_version],
    Content={
        'ZipFile': zipped_code
    },  
    Description='Lambda layer for pyarrow for daily Lambda function'
)
layer_arn = response['LayerVersionArn']
print("Lambda layer for pyarrow has been created << done")

# Create zip files for Lambda functions
print("Creating zip files for Daily Lambda function to ./zips ...") 
#-Daily function
with zipfile.ZipFile(lambdas['lambda_daily']['zip'], 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(lambdas['lambda_daily']['file'], arcname=lambdas['lambda_daily']['file'])
print("Zip files for Lambda functions have been created << done")
# Create Lambda functions
print("Creating Lambda functions ...")
    #-Daily function
with open(lambdas['lambda_daily']['zip'], 'rb') as f:
    zipped_code = f.read()
response = lambdaC.create_function(
    FunctionName='lambda_daily',
    Runtime=python_version,
    Role=role_arn,
    Layers=[layer_arn],
    Handler='lambda_daily.lambda_handler',
    Code={
        'ZipFile': zipped_code
    },
    Environment={
        'Variables': {
            'DYNAMODB_TABLE': dynamodb_name,
            'S3_BUCKET_NAME': S3_bucket_data
        }
    },
    MemorySize=1024, # 1 GB
    Timeout=60*2, # 2 minutes 
    Description='Fetches daily air quality data from DynamoDB and convert to AQI and store in S3 as Parquet'
)
dailyF_arn = response['FunctionArn'] # daily Lambda function ARN
print("Creating Daily Lambda function << done")
#******************Daily lambda creation above************************************#

print("Lambda functions have been created successfully... <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#
## EventBridge setup
print(f">>>>> {stage}/{total_stages} Setting up EventBridge rules to trigger Lambda functions...")
eventsC = session.client('events')

#***************Hourly lambda EventBridge creation below**************************#
# Set up EventBridge rule to trigger Lambda at HH:30
print(f"Setting up EventBridge rule to trigger Lambda function 'lambda_hourly' at HH:45...")
response = eventsC.put_rule(
    Name=hourly_rule_name,
    ScheduleExpression='cron(45 * * * ? *)',
    State='ENABLED',
    Description='Get hourly air quality data from sensor.community and store in DynamoDB'
)
hourlyR_arn = response['RuleArn'] # hourly EventBridge rule ARN
# Grant EventBridge permission to invoke the Lambda function
lambdaC.add_permission(
    FunctionName='lambda_hourly',
    StatementId='eventbridge-invoke-hourly-lambda',  # must be unique for each permission
    Action='lambda:InvokeFunction',
    Principal='events.amazonaws.com',
    SourceArn=hourlyR_arn
)
# Add Lambda function as the target of the EventBridge rule
eventsC.put_targets(
    Rule=hourly_rule_name,
    Targets=[{
        'Id': 'lambda_hourly_target',
        'Arn': hourlyF_arn
    }]
)
print("EventBridge rule to trigger Lambda function 'lambda_hourly' at HH:45 has been set... << done")
#***************Hourly lambda EventBridge creation above**************************#

#****************Daily lambda EventBridge creation below**************************#
# Set up EventBridge rule to trigger Lambda at 00:00 daily 
daily_rule_name = "lambda_daily_trigger"
print(f"Setting up EventBridge rule to trigger Lambda function 'lambda_daily' at 00:00 daily...")
response = eventsC.put_rule(    
    Name=daily_rule_name,
    ScheduleExpression='cron(0 0 * * ? *)',
    State='ENABLED',
    Description='Process daily air quality data from DynamoDB and store in S3 as Parquet'
)
dailyR_arn = response['RuleArn'] # daily EventBridge rule ARN
# Grant EventBridge permission to invoke the Lambda function
lambdaC.add_permission(
    FunctionName='lambda_daily',
    StatementId='eventbridge-invoke-daily-lambda',  # must be unique for each permission
    Action='lambda:InvokeFunction',
    Principal='events.amazonaws.com',
    SourceArn=dailyR_arn
)
# Add Lambda function as the target of the EventBridge rule
eventsC.put_targets(
    Rule=daily_rule_name,
    Targets=[{
        'Id': 'lambda_daily_target',
        'Arn': dailyF_arn
    }]
)
print("EventBridge rule to trigger Lambda function 'lambda_daily' at 00:00 daily has been set... << done")
#****************Daily lambda EventBridge creation above**************************#

print("EventBridge rules have been set to trigger Lambda functions <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#


s3C.upload_file(
        Filename = './frontend/index.html', 
        Bucket = S3_bucket_frontend, 
        Key = 'index.html', 
        ExtraArgs={'ContentType': 'text/html'}
        )

s3C.upload_file(
        Filename = './frontend/locations.json', 
        Bucket = S3_bucket_frontend, 
        Key = 'locations.json', 
        ExtraArgs={'ContentType': 'application/json'}
        )







print(">>>>> Setup completed successfully! <<<<<")
print("\n")
print(f"Website can be accessed at {website_url}")