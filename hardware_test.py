# -*- coding: utf-8 -*-

import boto3
from botocore.config import Config
with open('./credentials/credentials.txt', 'r') as file:
    lines = file.readlines()
    access_key = lines[1].split("=")[1].strip()
    secret_key = lines[2].split("=")[1].strip()
    token = lines[3].split("=")[1].strip()
region = 'us-east-1'

session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    aws_session_token=token,
    region_name=region
)

#s3 = session.client('s3')
#s3.create_bucket(Bucket='cloudcomputing-20251222')
#response = s3.list_buckets()

# Output the bucket names
#print('Existing buckets:')
#for bucket in response['Buckets']:
#    print(f'  {bucket["Name"]}')

instanceType = [
    "t3.micro",
    "t3.small",
    "t3a.medium",
    "t3.large",
    "c6a.large",
    "c6in.large"
]
instanceType = [
    "t3.micro"
]

ec2 = session.client('ec2')
#response = ec2.create_security_group(
#    GroupName='cloud-computing-CC',
#    Description='Security group for cloud-computing CC'
#)
#sg_id = response['GroupId']
#print(f"{sg_id=:}")#sg-059a0f09121671213
#ec2.authorize_security_group_ingress(
#    GroupId=sg_id,
#    IpPermissions=[
#        {
#            'IpProtocol': 'tcp',
#            'FromPort': 0,
#            'ToPort': 65535,
#            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allows all IPv4
#        }
#    ]
#)
myscript = '''#!/bin/bash
sudo yum update -y
sudo yum install -y python3 python3-pip
sudo pip3 install pandas pyarrow requests
curl -L https://raw.githubusercontent.com/Dsh219/MSc_CC_AirQuality/refs/heads/main/convert_AQI_ec2.py?token=GHSAT0AAAAAADQX2H6HIXZQDFT4ZJCUVKVC2KJSURA -o /home/ec2-user/script.py
cd /home/ec2-user
python3 script.py %s 
aws s3 cp ./%s.log s3://cloudcomputing-20251222/logs/%s.log

shutdown -h now

'''


for instance in instanceType:
    config = Config(
        retries = {
            'max_attempts': 10,
            'mode': 'standard'
        }
    )
    response = ec2.run_instances(
        ImageId='ami-068c0051b15cdb816',  #Amazon Linux 2023 AMI 2023.9.20251208.0 x86_64 HVM kernel-6.1 
        InstanceType=instance,
        MinCount=1,
        MaxCount=1,
        KeyName='vockey',
        SecurityGroups=['cloud-computing-CC'],
        Config=config,
        UserData=myscript % (instance, instance, instance)
    )

    print(f"Instance {instance} launched, ID: {response['Instances'][0]['InstanceId']}")

