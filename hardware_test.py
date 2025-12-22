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
# Define instance types to test
instanceType = [
    "t3.micro",
    "t3.small",
    "t3a.medium",
    "t3.large",
    "c6a.large",
    "c6in.large"
]
# EC2 client setup
config = Config(
        retries = {
            'max_attempts': 5,
            'mode': 'standard'
        }
    )
ec2 = session.client('ec2',config=config)
myscript = '''#!/bin/bash
yum update -y
yum install -y python3-pip
sudo curl -L %s -o /home/ec2-user/script.py
cd /home/ec2-user
python3 -m venv my_env
source my_env/bin/activate
pip3 install pandas pyarrow requests
python3 script.py %s 
aws s3 cp ./%s.log s3://cloudcomputing-20251222/logs/%s.log

shutdown -h now

'''
# Script URL
url = "https://raw.githubusercontent.com/Dsh219/MSc_CC_AirQuality/refs/heads/main/convert_AQI_ec2.py"
# Launch instances and run the script
for instance in instanceType:
    response = ec2.run_instances(
        ImageId='ami-068c0051b15cdb816',  #Amazon Linux 2023 AMI 2023.9.20251208.0 x86_64 HVM kernel-6.1 
        InstanceType=instance,
        MinCount=1,
        MaxCount=1,
        KeyName='vockey',
        SecurityGroups=['cloud-computing-CC'],
        IamInstanceProfile={
            'Name': 'LabInstanceProfile' 
        },
        UserData=myscript % (url,instance, instance, instance)
    )

    print(f"Instance {instance} launched, ID: {response['Instances'][0]['InstanceId']}")

