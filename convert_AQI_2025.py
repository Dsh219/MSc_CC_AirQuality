# -*- coding: utf-8 -*-
import requests
import os
import re
import pandas as pd
import time 
import logging



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

PM25_RANGES = [ (11, 1), (23, 2), (35, 3), (41, 4), (47, 5), 
               (53, 6), (58, 7), (64, 8), (70, 9), (float('inf'), 10) ]
PM10_RANGES = [ (16, 1), (33, 2), (50, 3), (58, 4), (66, 5), 
              (75, 6), (83, 7), (91, 8), (100, 9), (float('inf'), 10) ]

def aqi(value:float, ranges:list) -> int:
    for high, score in ranges:
        if value <= high:
            return score

def convert_AQI(url:str,date:str,sep:str=";",retries:int=4) -> list:
    for attempt in range(retries):
        try:
            df = pd.read_csv(url,sep=sep)
            break
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                logger.error(f"All {retries} attempts failed for URL: {url}")
                raise Exception(f"Failed to read CSV from {url} after {retries} attempts.")
    try:
        mean_p1 = df["P1"].mean()
    except TypeError: # in case of non-numeric data, e.g. unknown
        df["P1"] = pd.to_numeric(df["P1"], errors="coerce")
        mean_p1 = df["P1"].mean()
    try:
        mean_p2 = df["P2"].mean()
    except TypeError: # in case of non-numeric data, e.g. unknown
        df["P2"] = pd.to_numeric(df["P2"], errors="coerce") 
        mean_p2 = df["P2"].mean()
    aqi_p1 = 0
    if not pd.isna(mean_p1): # Check if mean_p1 is not NaN which means whole column is NaN
        aqi_p1 = aqi(mean_p1, PM10_RANGES)
    aqi_p2 = 0
    if not pd.isna(mean_p2):  # Check if mean_p2 is not NaN which means whole column is NaN
        aqi_p2 = aqi(mean_p2, PM25_RANGES)

    row = df.iloc[0]
    return [date,
            row.get("sensor_type", None),
            row.get("lat", None),
            row.get("lon", None),
            row.get("altitude", None),
            aqi_p1,
            aqi_p2
            ]

from datetime import date, timedelta
import os
start = date(2025, 1, 1)
end = date(2025, 3, 1)
monthly_data = []
current = start
while current < end:
    skip = False
    yr = current.year
    mo = f"{current.month:02d}"
    dy = f"{current.day:02d}"
    folder = f"https://archive.sensor.community/{yr}-{mo}-{dy}/"
    logger.info(f">>>>> Download a day folder from {folder}")
    
    for t in range(5):
        try:
            response = requests.get(folder)
            response.raise_for_status()  # raises error if request failed
            break
        except requests.exceptions.HTTPError as e:
            logger.error(f"Request failed: {e}")
            if t == 4:  
                skip = True
                logger.error(f"All 5 attempts failed for URL: {folder}")
    if skip:
        current += timedelta(days=1)
        continue
    
    html = response.text
    pattern = re.compile(r'<a href="([^"]+\.csv(?:\.gz)?)">', re.IGNORECASE)
    hrefs = pattern.findall(html)

    not_w = []
    i = 0
    a = 0

    st = time.time()
    for filename in hrefs:
        date_,Type,_ = filename.split("_",2)
        if Type.upper() in pmsensors:
            a+=1
            try:
                monthly_data.append(convert_AQI(folder + filename, date_))
                i+=1
                #if i == 2000:
                #    break
            except Exception as e:
                not_w.append(filename)

    dt = time.time() - st
    logger.info(f"Processed {i} out of {a} files in {dt:.2f} seconds. for date {current}")
    logger.info(f"Files not processed for {current}: {not_w}")
    current += timedelta(days=1)

    if mo != f"{current.month:02d}":
        folder_path = f"../s3/year={yr}/month={mo}"
        print(f"Finished {yr}={mo}")
        logger.info(f"Saving monthly results to {folder_path}/data.parquet")
        cols = ["date", "sensor_type", "lat", "lon", "altitude",  "PM10", "PM2_5"]
        ndf = pd.DataFrame(monthly_data, columns=cols)
        os.makedirs(folder_path, exist_ok=True)
        ndf.to_parquet(f"{folder_path}/data.parquet", engine="pyarrow", compression="snappy")
        monthly_data = []

    