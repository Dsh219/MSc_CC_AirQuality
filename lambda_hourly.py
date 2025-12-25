import json
import urllib.request as requests
import boto3
import time
from decimal import Decimal

def lambda_handler(event, context):
    url = "https://data.sensor.community/static/v2/data.1h.json"
    pmsensors = ["SDS011","SPS30","PMS5003","PMS7003",
        "PMS1003","HPM","PPD42NS","SDS021","PMS3003",
        "PMS6003","NEXTPM"]
    for t in range(5):  # Retry up to 5 times
        try:
            with requests.urlopen(url) as resp:
                data = json.loads(resp.read().decode())
            break 
        except:
            if t == 4:
                return {
                    "statusCode": 500,
                    "body": json.dumps("Failed to fetch data after multiple attempts.")
                }
            pass 

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("DailyAQI") # DynamoDB table name from setup.py
    num = 0
    with table.batch_writer() as batch:
        for Each in data:
            Type = Each['sensor']['sensor_type']['name']
            if Type.upper() in pmsensors:
                dic={}
                dic["PM10"] = 0
                dic["PM2_5"] = 0
                valid = False
                for measurement in Each['sensordatavalues']:
                    if measurement['value_type'] == "P1":
                        valid = True
                        try:
                            dic["PM10"] = Decimal(str(measurement['value']))
                        except Exception:
                            pass    
                    elif measurement['value_type'] == "P2":
                        valid = True
                        try:
                            dic["PM2_5"] = Decimal(str(measurement['value']))
                        except Exception:
                            pass
                if not valid:
                    continue

                dic["geo"] = f"{Each['location']['latitude']}_{Each['location']['longitude']}_{Each['id']}" # id duplicated using num instead
                dic["timestamp"] = f"{Each['timestamp'].replace(' ' ,'T')}" + "Z"
                dic["type"] = Type
                dic["altitude"] = Each['location'].get('altitude', "N/A")
                dic["expires_at"] = int(time.time() + 3600*24*2)  # 48 hours TTL
                batch.put_item(Item=dic)
                num += 1

    return {
        "statusCode": 200,
        "body": json.dumps(f"{num} items written to DynamoDB")
    }