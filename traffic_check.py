# -*- coding: utf-8 -*-

import requests
import json
import logging
import os
import re

scriptname = os.path.basename(__file__)

logname = f"./log/{scriptname}.log"

logger = logging.getLogger(__name__)
logging.basicConfig(filename=logname, 
                    encoding='utf-8',
                    filemode="w",
                    level=logging.INFO,
                    format = '%(name)s-%(levelname)s: %(message)s'
                    )

url = "https://data.sensor.community/static/v2/data.1h.json"

logger.info(f">>>>> Download last 1hr json data from {url}")
response = requests.get(url)
try:
    response.raise_for_status()  # raises error if request failed
except requests.exceptions.HTTPError as e:
    logger.error(f"Request failed: {e}")
    raise Exception(f"Download request failed, check log file for details --> {logname}")

raw_size = len(response.content)
data = response.json()
json_size = len(json.dumps(data).encode("utf-8"))
logger.info(f"Raw download: {raw_size / 1024 / 1024:.2f} MB")
logger.info(f"JSON serialized: {json_size / 1024 / 1024:.2f} MB")
logger.info(f"last 1hr json data from {url} size check complete <<<<<")
logger.info("------------------------------------------")

# Download a full day folder and calculate the size of PM sensor CSV files
folder = "https://archive.sensor.community/2025-12-19/"
logger.info(f">>>>> Download a day folder from {folder}")
with open("./data/PMsensors.json","r",encoding="utf-8") as f:
    pmsensors = json.load(f)
response = requests.get(folder)
try:
    response.raise_for_status()  # raises error if request failed
except requests.exceptions.HTTPError as e:
    logger.error(f"Request failed: {e}")
    raise Exception(f"Download request failed, check log file for details --> {logname}")

html = response.text

pattern = re.compile(
    r'<a href="([^"]+\.csv(?:\.gz)?)">[^<]+</a></td>.*?<td align="right">\s*([\d\.]+[KM]?)\s*</td>',
    re.DOTALL
)
matches = pattern.findall(html)
size = 0
for filename, size_str in matches:
    if filename.split("_")[1].upper() in pmsensors:
        if size_str.endswith("K"):
            size += float(size_str[:-1]) * 1024
        elif size_str.endswith("M"):
            size += float(size_str[:-1]) * 1024 * 1024
        else:
            size += float(size_str)

#print(f"Total size of PM sensor CSV files for a day: {size / 1024 / 1024:.2f} MB")
logger.info(f"Total size of PM sensor CSV files for a day: {size / 1024 / 1024:.2f} MB")
logger.info(f"Day folder from {folder} size check complete <<<<<")
