# -*- coding: utf-8 -*-
print(">>>>> Starting setup <<<<<")
print(">>>>> Starting setup <<<<<")
import boto3
from botocore.config import Config
import zipfile
import json
from pathlib import Path
import time
stage = 1
total_stages = 10
#---------------------------------------------------------------------------------#
#-----------------------Load credentials and define vars--------------------------#
#---------------------------------------------------------------------------------#
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
S3_bucket_data = 'cloudcomputing-20260101'   # has to be globally unique
local_data_folder = './data/s3'
athena_output = f's3://{S3_bucket_data}/output/'  # S3 bucket for Athena query results
athena_root = f's3://{S3_bucket_data}/data/'    # S3 bucket for Athena root
athena_name = 'daily_aqi'  # Athena table name
S3_bucket_frontend = 'cloud-computing-frontend-20260101'  # has to be globally unique
EC2_security_group_name = 'cloud-computing-CC'
dynamodb_name = 'DailyAQI'
GSI_name = 'dailyindex'
role_name = "LabRole"
# EventBridge rule names
hourly_rule_name = "lambda_hourly_trigger"
daily_rule_name = "lambda_daily_trigger"
# API Gateway names
API_name = "AirQualityAPI"
stage_name = "dev"
# endpoint for S3 website hosting
s3_web_endpoint = "s3-website-us-east-1.amazonaws.com" # for US East (N. Virginia) region us-east-1, details at https://docs.aws.amazon.com/general/latest/gr/s3.html#s3_website_region_endpoints

# Define Lambda functions and their zip file paths
lambdas = {
    'lambda_hourly': {
        'zip': './zips/lambda_hourly.zip',
        'file': 'lambda_hourly.py',
        'name': 'lambda_hourly'
    },
    'lambda_daily': {
        'zip': './zips/lambda_daily.zip',
        'file': 'lambda_daily.py',
        'name': 'lambda_daily'
    },
    'pyarrow-layer': {
        'zip': './zips/daily-layer.zip', # Lambda layer for pyarrow, has to be compressed by a Linux system
        'name': 'pyarrow-layer'
    },
    'request_24hrs': {
        'zip': './zips/lambda_Rq_24hrs.zip',
        'file': 'lambda_Rq_24hrs.py',
        'name': 'lambda_request_24hrs'
    },
    'request_archive': {
        'zip': './zips/lambda_Rq_arch.zip', 
        'file': 'lambda_Rq_arch.py',
        'name': 'lambda_request_archive'
    }
}                                                        
print("AWS credentials and vars loaded <<<<< done")
stage += 1

print(f"\n>>>>> {stage}/{total_stages} Creating AWS session...")
session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    aws_session_token=token,
    region_name=region
)
print("AWS session created <<<<< done")
stage += 1
'''
#---------------------------------------------------------------------------------#
#-------------------------Link Athena table to the S3-----------------------------#
#---------------------------------------------------------------------------------#
print(f"\n>>>>>> {stage}/{total_stages} Linking Athena table to the S3 bucket {S3_bucket_data}...")
athenaC = session.client('athena')
query = f"""
CREATE EXTERNAL TABLE IF NOT EXISTS {athena_name} (
    Rdate STRING,
    lat STRING,
    lon STRING,
    AQI INT
)
PARTITIONED BY (year INT, month INT, day INT)
STORED AS PARQUET
LOCATION '{athena_root}'
"""
response = athenaC.start_query_execution(   
    QueryString=query,
    QueryExecutionContext={"Database": "default"},
    ResultConfiguration={"OutputLocation": athena_output}
)
while True:
    query_status = athenaC.get_query_execution(QueryExecutionId=response['QueryExecutionId'])
    
    query_state = query_status['QueryExecution']['Status']['State']
    if query_state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
        break
    time.sleep(2)
if query_state != 'SUCCEEDED':
    if query_state in ['FAILED', 'CANCELLED']:
        reason = query_status['QueryExecution']['Status'].get(
            'StateChangeReason', 'Unknown reason'
        )
    print(f"Query {query_state}: {reason}")
    raise Exception(f"Setup stopped! => Failed to link Athena table to the S3 bucket {S3_bucket_data} : Query {query_state}")

response = athenaC.start_query_execution(
    QueryString=f"MSCK REPAIR TABLE {athena_name}",
    QueryExecutionContext={"Database": "default"},
    ResultConfiguration={"OutputLocation": athena_output}
)
while True:
    query_status = athenaC.get_query_execution(QueryExecutionId=response['QueryExecutionId'])
    query_state = query_status['QueryExecution']['Status']['State']
    if query_state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
        break
    time.sleep(2)
if query_state != 'SUCCEEDED':
    
    if query_state in ['FAILED', 'CANCELLED']:
        reason = query_status['QueryExecution']['Status'].get(
            'StateChangeReason', 'Unknown reason'
        )
    print(f"Query {query_state}: {reason}")
    raise Exception(f"Setup stopped! => Failed to link Athena table to the S3 bucket {S3_bucket_data} : Query {query_state}")

print(f"Athena table has been linked to the S3 bucket {S3_bucket_data} <<<<< done")
# url => http://cloud-computing-frontend-20260101.s3-website-us-east-1.amazonaws.com
'''

s3C = session.client('s3')
for folder in Path(local_data_folder).iterdir():
    if folder.is_dir():
        Fname = folder.name 
        yr,mo,dy = Fname.split('=')[1].split('-')
        pq_file = list(folder.glob('*.parquet'))[0]
        s3_key = f"data/year={yr}/month={mo}/day={dy}/data.parquet"
        s3C.upload_file(
            Filename = str(pq_file), 
            Bucket = S3_bucket_data, 
            Key = s3_key, 
            ExtraArgs={'ContentType': 'application/parquet'}
            )
        print(f"\r{Fname}", end='')
print("\nAll data parquet files have been uploaded to S3 data bucket.")