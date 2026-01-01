import boto3 
from boto3.dynamodb.conditions import Key
import os
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ["DYNAMODB_TABLE"]) # DynamoDB table name from setup.py
GSI_name = os.environ["GSI_NAME"]  # GSI name from setup.py

def lambda_handler(event, context):
    if 'queryStringParameters' not in event:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing query parameters')
        }
    lat = event['queryStringParameters'].get('lat')
    lon = event['queryStringParameters'].get('lon')
    if lat is None or lon is None:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing lat or lon parameter')
        }
    try:
        response = table.query(
            IndexName=GSI_name, 
            KeyConditionExpression=Key('location').eq(f"{lat}_{lon}")   
            )
        items = response.get('Items', [])
        return {
            'statusCode': 200,
            'body': json.dumps(items)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error querying data: {str(e)}")
        }
    
    