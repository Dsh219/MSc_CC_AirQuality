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
S3_bucket_data = 'cloudcomputing-20251231'   # has to be globally unique
S3_bucket_frontend = 'cloud-computing-frontend-20251231'  # has to be globally unique
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
'''
## S3 setup
print(f">>>>> {stage}/{total_stages} Creating S3 buckets")
s3C = session.client('s3')

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
                    'AllowedOrigins': ["http://cloud-computing-frontend-20251231.s3-website-us-east-1.amazonaws.com"],
                    'MaxAgeSeconds': 3000
                    }
                ]
            }
        )
except Exception as e:
    raise Exception(f"Setup stopped! => Failed to create S3 bucket with name= {S3_bucket_data} : {e}")
print(f"S3 bucket for data with name= {S3_bucket_data} has been created successfully with traffic restrictions only from frontend... <<done")
#******************Data S3 bucket creation above***********************************#
'''
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

# url => http://cloud-computing-frontend-20251231.s3-website-us-east-1.amazonaws.com