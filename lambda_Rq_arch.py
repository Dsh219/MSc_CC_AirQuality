import boto3 
import os
s3 = boto3.resource('s3')
bucket_name = os.environ["S3_BUCKET_DATA"]  # S3 bucket name from setup.py