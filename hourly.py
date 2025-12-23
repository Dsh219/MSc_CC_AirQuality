import json
import urllib.request as requests
import boto3
import time

def lambda_handler(event, context):
    url = "https://data.sensor.community/static/v2/data.1h.json"
    pmsensors = ["SDS011","SPS30","PMS5003","PMS7003",
        "PMS1003","HPM","PPD42NS","SDS021","PMS3003",
        "PMS6003","NextPM"]
    PM25_RANGES = [ (11, 1), (23, 2), (35, 3), (41, 4), (47, 5), 
               (53, 6), (58, 7), (64, 8), (70, 9), (float('inf'), 10) ]
    PM10_RANGES = [ (16, 1), (33, 2), (50, 3), (58, 4), (66, 5), 
                (75, 6), (83, 7), (91, 8), (100, 9), (float('inf'), 10) ]

    def aqi(value:float|int, ranges:list) -> int:
        for high, score in ranges:
            if value <= high:
                return score

    with requests.urlopen(url) as resp:
        data = json.loads(resp.read().decode())
    write_data = []
    for Each in data:
        if Each['sensor']['sensor_type']['name'] in pmsensors:
            dic={}
            dic["geo"] = f"{Each['location']['latitude']}_{Each['location']['longitude']}_{Each['id']}"
            dic["timestamp"] = f"{Each['timestamp'].replace(" ","T")}" + "Z"
            for measurement in Each['sensordatavalues']:
                dic["PM10"] = 0
                dic["PM2.5"] = 0
                if measurement['value_type'] == "P1":
                    dic["PM10"] = aqi(measurement['value'], PM10_RANGES)
                elif measurement['value_type'] == "P2":
                    dic["PM2.5"] = aqi(measurement['value'], PM25_RANGES)
            dic["altitude"] = Each['location'].get('altitude', "N/A")
            dic["expires_at"] = int(time.time() + 3600*24) 

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("MyTable")
    
    with table.batch_writer() as batch:
        for item in data:
            batch.put_item(Item=item)
    
    return {
        "statusCode": 200,
        "body": json.dumps(f"{len(data)} items written to DynamoDB")
    }