# -*- coding: utf-8 -*-

import boto3
from botocore.config import Config
# read credentials
#with open('./credentials/credentials.txt', 'r') as file:
with open('../credentials.txt', 'r') as file:
    lines = file.readlines()
    access_key = lines[1].split("=")[1].strip()
    secret_key = lines[2].split("=")[1].strip()
    token = lines[3].split("=")[1].strip()
region = 'us-east-1'
# Create a session
session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    aws_session_token=token,
    region_name=region
)
#'''
## Define vars for setup
S3_name = 'cloudcomputing-20251222'   # has to be globally unique
EC2_security_group_name = 'cloud-computing-CC'
dynamodb_name = 'DailyAQI'

## S3 setup
print(f">>>>> Creating S3 bucket with name= {S3_name}")
s3 = session.client('s3')
s3.create_bucket(Bucket=S3_name) 
print(f"S3 bucket with name= {S3_name} has been created successfully... <<<<< done")

# EC2 security group setup
print(f">>>>> Creating EC2 security group with name= {EC2_security_group_name}")
config = Config(
        retries = {
            'max_attempts': 5,
            'mode': 'standard'
        }
    )
ec2 = session.client('ec2',config=config)
response = ec2.create_security_group(
    GroupName=EC2_security_group_name,
    Description='Security group for cloud-computing CC'
)
sg_id = response['GroupId']
# setting inbound rules
print(f"Setting inbound rules for security group - {EC2_security_group_name} with id= {sg_id} ...")
ec2.authorize_security_group_ingress(
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

## DynamoDB setup
print(f">>>>> Creating DynamoDB table with name= {dynamodb_name}")
dynamodb = session.client('dynamodb')
table = dynamodb.create_table(
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
waiter = dynamodb.get_waiter('table_exists')
waiter.wait(TableName=dynamodb_name)
print(f"{dynamodb_name} has been created successfully...")
# Enable TTL on the table
dynamodb.update_time_to_live(
    TableName=dynamodb_name,
    TimeToLiveSpecification={
        'Enabled': True,
        'AttributeName': 'expires_at'
    }   
)
print(f"{dynamodb_name} has been assigned TTL...")
print(f"Creating DynamoDB table with name= {dynamodb_name} <<<<< done")
#''' 
