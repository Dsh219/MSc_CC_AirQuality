# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18 22:24:54 2025

@author: 19722
"""

import requests
import json
import logging

json_name_1hr = "1hr_json.json"
logname = "last_hour_json_summary.log"

logger = logging.getLogger(__name__)
logging.basicConfig(filename=logname, 
                    encoding='utf-8',
                    filemode="w",
                    level=logging.INFO,
                    format = '%(name)s-%(levelname)s: %(message)s'
                    )

url = "https://data.sensor.community/static/v2/data.1h.json"

# download a copy 
logger.info(f">>>>> Download last 1hr json data from {url}")
response = requests.get(url)
try:
    response.raise_for_status()  # raises error if request failed
except requests.exceptions.HTTPError as e:
    logger.error(f"Request failed: {e}")
    raise Exception(f"Download request failed, check log file for details --> {logname}")

data = response.json()
with open(json_name_1hr, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
logger.info("Last 1hr json is downloaded <<<<<")

# check the characteritics
logger.info(f">>>>> Read downloaded json from {json_name_1hr}")
with open(json_name_1hr, "r", encoding="utf-8") as f:
    json_1h = json.load(f)
    
logger.info(f"{type(json_1h)=:}") # check the data format in the josn downloaded
number_entry = len(json_1h)
logger.info(f"{number_entry=:}")

# Examine the structure of the json
has_sensor = 0     
has_sensor_type = 0
has_sensor_type_name = 0
for entry in json_1h:
    if "sensor" in entry:
        has_sensor += 1
        if "sensor_type" in entry["sensor"]:
            has_sensor_type += 1
            if "name" in entry["sensor"]["sensor_type"]:
                has_sensor_type_name += 1

logger.info(f"all entry has <sensor> key: {has_sensor == number_entry}")
logger.info(f"all entry has <sensor:sensor_type> key: {has_sensor_type == number_entry}")
logger.info(f"all entry has <sensor:sensor_type:name> key: {has_sensor_type_name == number_entry}")

sensors = {}
for entry in json_1h:
    sensor_name = entry["sensor"]["sensor_type"]["name"]
    if sensor_name not in sensors:
        sensors[sensor_name] = 1
    else:
        sensors[sensor_name] += 1
logger.info("Sensors summary:")
logger.info(sensors)
logger.info(f"number of sensors matches: {sum(sensors.values()) == number_entry }")
logger.info(sensors.keys())

sensors_filename = "sensors_types_1hr.txt"
logger.info(f">>>>> Writing sensor types with check box to a txt file --- {sensors_filename}")
with open(sensors_filename,"w",encoding="utf-8") as f:
    for typ in sensors.keys():
        f.write(f"[ ] {typ}\n")
logger.info(f"{sensors_filename} is written <<<<")


