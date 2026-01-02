import json
import boto3
from decimal import Decimal
from collections import defaultdict
import pyarrow as pa
import pyarrow.parquet as pq
import io
import time
import os 
def aqi(value:Decimal, ranges:list) -> int:
    for high, score in ranges:
        if value <= high:
            return score

pmsensors = ["SDS011","SPS30","PMS5003","PMS7003",
        "PMS1003","HPM","PPD42NS","SDS021","PMS3003",
        "PMS6003","NEXTPM"]

PM25_RANGES = [ (Decimal(11), 1), (Decimal(23), 2), (Decimal(35), 3), (Decimal(41), 4), (Decimal(47), 5), 
            (Decimal(53), 6), (Decimal(58), 7), (Decimal(64), 8), (Decimal(70), 9), (Decimal('inf'), 10) ]
PM10_RANGES = [ (Decimal(16), 1), (Decimal(33), 2), (Decimal(50), 3), (Decimal(58), 4), (Decimal(66), 5), 
            (Decimal(75), 6), (Decimal(83), 7), (Decimal(91), 8), (Decimal(100), 9), (Decimal('inf'), 10) ]


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DYNAMODB_TABLE"]) # DynamoDB table name from setup.py <======        
s3 = boto3.client('s3')
s3_bucketname = os.environ["S3_BUCKET_NAME"]  # S3 bucket name from setup.py <======
athena = boto3.client('athena')
athena_output = os.environ["ATHENA_OUTPUT"]  # Athena output S3 bucket from
athena_root = os.environ["ATHENA_ROOT"]  # Athena root S3 bucket from setup.py
athena_name = os.environ["ATHENA_NAME"]  # Athena table name from setup.py

def lambda_handler(event, context):

    grouped = defaultdict(lambda: {'PM10': [], 'PM2_5': []})
    response = table.scan()
    if not response['Items']:
        return {
            "statusCode": 200,
            "body": json.dumps("No data available for processing.")
        }
    date = response['Items'][0]['timestamp'].split('T')[0]  # teimstamp => YYYY-MM-DDTHH:MM:SSZ
    while True:
        for item in response['Items']:
            lat, lon , id = item['geo'].split('_')
            key = (lat, lon, item.get('altitude', None))
            if item.get('PM10', 0) > 0:
                grouped[key]['PM10'].append(item['PM10'])
            if item.get('PM2_5', 0) > 0:
                grouped[key]['PM2_5'].append(item['PM2_5'])
        if 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        else:
            break
    all = []
    for (lat, lon, altitude), measures in grouped.items():
        aqi_pm10 = aqi(sum(measures['PM10']) / len(measures['PM10']), PM10_RANGES) if measures['PM10'] else 0
        aqi_pm2_5 = aqi(sum(measures['PM2_5']) / len(measures['PM2_5']), PM25_RANGES) if measures['PM2_5'] else 0
        AQI = max(aqi_pm10, aqi_pm2_5)
        #entry = {
        #    'date': date,
        #    'lat': lat,
        #    'lon': lon,
        #    'altitude': altitude if altitude is not None else "N/A",
        #    'AQI':AQI
        #}
        entry = {
            'lat': lat,
            'lon': lon,
            'AQI':AQI
        }
        all.append(entry)
    num = len(all)
    ## Write to S3 as Parquet
    # Define schema
    #schema = pa.schema([
    #    ('date', pa.string()),
    #    ('lat', pa.string()),
    #    ('lon', pa.string()),
    #    ('altitude', pa.string()),
    #    ('AQI', pa.int32())
    #])
    schema = pa.schema([
        ('lat', pa.string()),
        ('lon', pa.string()),
        ('AQI', pa.int32())
    ])
    pa_table = pa.Table.from_pylist(all,schema=schema)
    parquet_buffer = io.BytesIO()
    pq.write_table(pa_table, parquet_buffer)
    yr,mo,dy = date.split('-')
    for times in range(5):  # Retry up to 5 times
        try:    
            s3.put_object(Bucket=s3_bucketname, 
                      Key=f'data/year={yr}/month={mo}/day={dy}/data.parquet', 
                      Body=parquet_buffer.getvalue())
            break
        except Exception as e:
            if times == 4:
                return {
                    "statusCode": 500,
                    "body": json.dumps(f"Failed to write Parquet to S3: {e}")
                }
            time.sleep(1.5 ** times) 
    # Update athena table
    query = f"""
    ALTER TABLE {athena_name} ADD IF NOT EXISTS
    PARTITION (year={int(yr)}, month={int(mo)}, day={int(dy)})
    LOCATION '{athena_root}year={yr}/month={mo}/day={dy}/'
    """
    response=athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": "default"},
        ResultConfiguration={"OutputLocation": athena_output}
    )
    return {
        "statusCode": 200,
        "body": json.dumps(f"{num} items written to S3 as Parquet")
    }