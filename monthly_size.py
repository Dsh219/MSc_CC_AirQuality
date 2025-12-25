# -*- coding: utf-8 -*-

import requests
import logging
import os
import re
from datetime import date

scriptname = os.path.basename(__file__)
logname = f"./log/{scriptname}.log"
logger = logging.getLogger(__name__)
logging.basicConfig(filename=logname, 
                    encoding='utf-8',
                    filemode="w",
                    level=logging.INFO,
                    format = '%(name)s-%(levelname)s: %(message)s'
                    )
pmsensors = [
 "SDS011",
 "SPS30",
 "PMS5003",
 "PMS7003",
 "PMS1003",
 "HPM",
 "PPD42NS",
 "SDS021",
 "PMS3003",
 "PMS6003",
 "NEXTPM"
]
# Download a full day folder and calculate the size of PM sensor CSV files
folder = "https://archive.sensor.community/csv_per_month/"
logger.info(f">>>>> Accessing info from {folder}")

# Loop over months
start = date(2015, 10, 1)
end = date(2025, 12, 1)
current = start
size = 0 # total size in bytes
msize = 0 # used to calculate monthly size
while current < end:
    msize = size
    skip = False
    yr = current.year
    mo = f"{current.month:02d}"
    for t in range(5):
        try:
            response = requests.get(folder + f"{yr}-{mo}/")
            response.raise_for_status()  # raises error if request failed
            break
        except Exception as e:
            logger.error(f"Request failed on {folder} time = {t}: {e}")
            if t == 4:
                logger.error(f"All {t} times Request failed on {folder}: {e}")
                skip = True
    if skip:
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
        continue
    # Parse HTML to find zip files and their sizes
    html = response.text
    pattern = re.compile(
        r'<a href="([^"]+\.zip(?:\.gz)?)">[^<]+</a></td>.*?<td align="right">\s*([\d\.]+[GKM]?)\s*</td>',
        re.DOTALL
    )
    matches = pattern.findall(html)
    for filename, size_str in matches:
        ty = filename.split("_")[1].split(".")[0].upper()  
        if ty in pmsensors: # Only consider PM sensor files
            if size_str.endswith("K"):
                size += float(size_str[:-1]) * 1024
            elif size_str.endswith("M"):
                size += float(size_str[:-1]) * 1024 * 1024
            elif size_str.endswith("G"):
                size += float(size_str[:-1]) * 1024 * 1024 * 1024
            else:
                size += float(size_str)
    logger.info(f"Total size of PM sensor zip files for {yr}-{mo}: {(size -msize) / 1024 / 1024/1024:.2f} GB")
    # Next day
    if current.month == 12:
        current = date(current.year + 1, 1, 1)
    else:
        current = date(current.year, current.month + 1, 1)

logger.info(f"Total size for PM zip files are {size/1024/1024/1024:.2f} GB")

