# -*- coding: utf-8 -*-
print(">>>>> Starting setup <<<<<")
import boto3
from botocore.config import Config
import zipfile
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
S3_name = 'cloudcomputing-20251222'   # has to be globally unique
EC2_security_group_name = 'cloud-computing-CC'
dynamodb_name = 'DailyAQI'
role_name = "LabRole"
hourly_rule_name = "lambda_hourly_trigger"
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
'''
#---------------------------------------------------------------------------------#
## S3 setup
print(f">>>>> {stage}/{total_stages} Creating S3 bucket with name= {S3_name}")
s3C = session.client('s3')
try:
    s3C.create_bucket(Bucket=S3_name) 
except Exception as e:
    raise Exception(f"Setup stopped! => Failed to create S3 bucket with name= {S3_name} : {e}")
print(f"S3 bucket with name= {S3_name} has been created successfully... <<<<< done")
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
''' 
## Lambda setup
print(f">>>>> {stage}/{total_stages} Creating Lambda functions...")
lambdaC = session.client('lambda')
# Define Lambda functions and their zip file paths
lambdas = {
    'lambda_hourly': {
        'zip': './zips/lambda_hourly.zip',
        'file': 'lambda_hourly.py' 
    }
}
# Create zip files for Lambda functions
print("Creating zip files for Lambda functions to ./zips ...")
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
    Runtime='python3.10',
    Role=role_arn,
    Handler='lambda_hourly.lambda_handler',
    Code={
        'ZipFile': zipped_code
    },
    Timeout=60*2, # 2 minutes > 
    Description='Fetches hourly air quality data and stores in DynamoDB'
)
hourlyF_arn = response['FunctionArn'] # hourly Lambda function ARN
print("Creating Lambda functions << done")
print("Lambda functions have been created successfully... <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#
## EventBridge setup
print(f">>>>> {stage}/{total_stages} Setting up EventBridge rules to trigger Lambda functions...")
eventsC = session.client('events')

# Set up EventBridge rule to trigger Lambda at HH:30
print(f"Setting up EventBridge rule to trigger Lambda function 'lambda_hourly' at HH:30...")
response = eventsC.put_rule(
    Name=hourly_rule_name,
    ScheduleExpression='cron(30 * * * ? *)',
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
print("EventBridge rule to trigger Lambda function 'lambda_hourly' at HH:30 has been set... << done")
print("EventBridge rules have been set to trigger Lambda functions <<<<< done")
stage += 1
#---------------------------------------------------------------------------------#
print(">>>>> Setup completed successfully! <<<<<")