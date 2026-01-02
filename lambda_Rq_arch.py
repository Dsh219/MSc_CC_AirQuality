import boto3 
import os
import json

s3 = boto3.resource('s3')
athena = boto3.client('athena')
bucket_name = os.environ["S3_BUCKET_DATA"]  # S3 bucket name from setup.py
athena_name = os.environ["athena_name"]  # Athena table name from setup.py
athena_output = os.environ["ATHENA_OUTPUT"]  # Athena output S3 bucket from setup.py

def lambda_handler(event, context):
    if 'queryStringParameters' not in event:
        return {
            'statusCode': 400,
            'body': json.dumps('Missing query parameters')
        }
    lat = event['queryStringParameters'].get('lat')
    lon = event['queryStringParameters'].get('lon')

    date0 = event['queryStringParameters'].get('date0')
    date1 = event['queryStringParameters'].get('date1')
    if lat is None or lon is None or date0 is None or date1 is None:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps('Missing one or more required query parameters: lat, lon, date0, date1')
        }
    query = f"""
        SELECT * FROM {athena_name}
        WHERE 
            from_iso8601_date(format('%04d-%02d-%02d', year, month, day))
            BETWEEN date '{date0}' AND date '{date1}'
            AND lat = '{lat}'
            AND lon = '{lon}'
    """


















    # Download the input file from S3
    s3.Bucket(bucket_name).download_file(input_key, '/tmp/input_file.csv')

    # Process the file (dummy processing here)
    with open('/tmp/input_file.csv', 'r') as infile, open('/tmp/output_file.csv', 'w') as outfile:
        for line in infile:
            # Example processing: convert to uppercase
            outfile.write(line.upper())

    # Upload the processed file back to S3
    s3.Bucket(bucket_name).upload_file('/tmp/output_file.csv', output_key)

    return {
        'statusCode': 200,
        'body': f'Processed file saved to {output_key}'
    }