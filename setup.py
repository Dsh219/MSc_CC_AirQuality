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
# Define vars for setup
S3_name = 'cloudcomputing-20251222'   # has to be globally unique
EC2_security_group_name = 'cloud-computing-CC'
# S3 setup
s3 = session.client('s3')
s3.create_bucket(Bucket=S3_name) 
# EC2 security group setup
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