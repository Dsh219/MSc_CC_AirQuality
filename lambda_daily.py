import json
import boto3
from decimal import Decimal
from collections import defaultdict
import pyarrow as pa
import pyarrow.parquet as pq
import io
import time

pmsensors = ["SDS011","SPS30","PMS5003","PMS7003",
        "PMS1003","HPM","PPD42NS","SDS021","PMS3003",
        "PMS6003","NEXTPM"]

PM25_RANGES = [ (Decimal(11), 1), (Decimal(23), 2), (Decimal(35), 3), (Decimal(41), 4), (Decimal(47), 5), 
            (Decimal(53), 6), (Decimal(58), 7), (Decimal(64), 8), (Decimal(70), 9), (Decimal('inf'), 10) ]
PM10_RANGES = [ (Decimal(16), 1), (Decimal(33), 2), (Decimal(50), 3), (Decimal(58), 4), (Decimal(66), 5), 
            (Decimal(75), 6), (Decimal(83), 7), (Decimal(91), 8), (Decimal(100), 9), (Decimal('inf'), 10) ]

def aqi(value:Decimal, ranges:list) -> int:
    for high, score in ranges:
        if value <= high:
            return score
        
def lambda_handler(event, context):

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("DailyAQI") # DynamoDB table name from setup.py <======
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
        entry = {
            'date': date,
            'lat': float(lat),
            'lon': float(lon),
            'altitude': float(altitude) if altitude is not None else float('nan'),
            'AQI':AQI
        }
        all.append(entry)
    num = len(all)
    ## Write to S3 as Parquet
    # Define schema
    schema = pa.schema([
        ('date', pa.string()),
        ('lat', pa.float64()),
        ('lon', pa.float64()),
        ('altitude', pa.float64()),
        ('AQI', pa.int32())
    ])
    pa_table = pa.Table.from_pylist(all,schema=schema)
    parquet_buffer = io.BytesIO()
    pq.write_table(pa_table, parquet_buffer)
    yr,mo,dy = date.split('-')
    s3 = boto3.client('s3')
    for times in range(5):  # Retry up to 5 times
        try:    
            s3.put_object(Bucket='cloudcomputing-20251222',  # S3 bucket name from setup.py <======
                      Key=f'year={yr}/month={mo}/day={dy}/data.parquet', 
                      Body=parquet_buffer.getvalue())
            break
        except Exception as e:
            if times == 4:
                return {
                    "statusCode": 500,
                    "body": json.dumps(f"Failed to write Parquet to S3: {e}")
                }
            time.sleep(1.5 ** times) 
    return {
        "statusCode": 200,
        "body": json.dumps(f"{num} items written to S3 as Parquet")
    }