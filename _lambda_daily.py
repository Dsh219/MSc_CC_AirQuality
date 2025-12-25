import json
import urllib.request as requests
import boto3
import time


def lambda_handler(event, context):
    pmsensors = ["SDS011","SPS30","PMS5003","PMS7003",
        "PMS1003","HPM","PPD42NS","SDS021","PMS3003",
        "PMS6003","NEXTPM"]
    PM25_RANGES = [ (11, 1), (23, 2), (35, 3), (41, 4), (47, 5), 
               (53, 6), (58, 7), (64, 8), (70, 9), (float('inf'), 10) ]
    PM10_RANGES = [ (16, 1), (33, 2), (50, 3), (58, 4), (66, 5), 
                (75, 6), (83, 7), (91, 8), (100, 9), (float('inf'), 10) ]
    def aqi(value:float, ranges:list) -> int:
        for high, score in ranges:
            if value <= high:
                return score
            
    base_url = "https://archive.sensor.community/"    
            
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
                dic["geo"] = f"{Each['location']['latitude']}_{Each['location']['longitude']}_{num}" # id duplicated using num instead
                dic["timestamp"] = f"{Each['timestamp'].replace(' ' ,'T')}" + "Z"
                dic["type"] = Type
                dic["PM10"] = 0
                dic["PM2.5"] = 0
                for measurement in Each['sensordatavalues']:
                    if measurement['value_type'] == "P1":
                        try:
                            dic["PM10"] = aqi(float(measurement['value']), PM10_RANGES)
                        except Exception:
                            pass    
                    elif measurement['value_type'] == "P2":
                        try:
                            dic["PM2.5"] = aqi(float(measurement['value']), PM25_RANGES)
                        except Exception:
                            pass
                dic["altitude"] = Each['location'].get('altitude', "N/A")
                dic["expires_at"] = int(time.time() + 3600*24)  # 24 hours TTL
                batch.put_item(Item=dic)
                num += 1

    return {
        "statusCode": 200,
        "body": json.dumps(f"{num} items written to DynamoDB")
    }