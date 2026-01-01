import boto3 
import os
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ["DYNAMODB_TABLE"]) # DynamoDB table name from setup.py

def lambda_handler(event, context):

    lat = event['queryStringParameters'].get('lat')
    lon = event['queryStringParameters'].get('lon')
    if lat is None or lon is None:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing lat or lon parameter')
        }
    
    # Query DynamoDB for the last 24 hours of data for the given lat/lon
    response = table.query(
        IndexName='lat-lon-index',  # Assuming a GSI on lat and lon
        KeyConditionExpression=boto3.dynamodb.conditions.Key('lat').eq(lat) & 
                               boto3.dynamodb.conditions.Key('lon').eq(lon),
        FilterExpression=boto3.dynamodb.conditions.Attr('timestamp').gte(int(time.time()) - 86400)
    )
    
    items = response.get('Items', [])
    
    return {
        'statusCode': 200,
        'body': json.dumps(items)
    }