# -*- coding: utf-8 -*-
import requests
import json
import os
import re
import pandas as pd
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
with open("./data/PMsensors.json","r",encoding="utf-8") as f:
    pmsensors = json.load(f)

PM = {
    "P1" : "PM10",
    "P2" : "PM2.5"
}

AQI = {
    "PM2.5" : {
         "0<=%f<=11" : 1,
        "12<=%f<=23" : 2,
        "24<=%f<=35" : 3,
        "36<=%f<=41" : 4,
        "42<=%f<=47" : 5,
        "48<=%f<=53" : 6,
        "54<=%f<=58" : 7,
        "59<=%f<=64" : 8,
        "65<=%f<=70" : 9,
        "71<=%f" : 10
    },
    "PM10" : {
         "0<=%f<=16" : 1,
        "17<=%f<=33" : 2,
        "34<=%f<=50" : 3,
        "51<=%f<=58" : 4,
        "59<=%f<=66" : 5,
        "67<=%f<=75" : 6,
        "76<=%f<=83" : 7,
        "84<=%f<=91" : 8,
        "92<=%f<=100" : 9,
       "101<=%f" : 10
    }
}

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
    aqi_p1 = "NA"
    if not pd.isna(mean_p1): # Check if mean_p1 is not NaN which means whole column is NaN
        for condition in AQI[PM["P1"]].keys():
            if eval(condition%mean_p1):
                aqi_p1 = AQI[PM["P1"]][condition]
                break
    aqi_p2 = "NA"
    if not pd.isna(mean_p2):  # Check if mean_p2 is not NaN which means whole column is NaN
        for condition in AQI[PM["P2"]].keys():
            if eval(condition%mean_p2):
                aqi_p2 = AQI[PM["P2"]][condition]
                break
    row = df.iloc[0]
    return [row.get("sensor_id", None),
            row.get("sensor_type", None),
            row.get("location", None),
            row.get("lat", None),
            row.get("lon", None),
            row.get("altitude", None),
            date,
            aqi_p1,
            aqi_p2
            ]

folder = "https://archive.sensor.community/2025-12-19/"
logger.info(f">>>>> Download a day folder from {folder}")
response = requests.get(folder)
try:
    response.raise_for_status()  # raises error if request failed
except requests.exceptions.HTTPError as e:
    logger.error(f"Request failed: {e}")
    raise Exception(f"Download request failed, check log file for details --> {logname}")
html = response.text
pattern = re.compile(r'<a href="([^"]+\.csv(?:\.gz)?)">', re.IGNORECASE)
hrefs = pattern.findall(html)

l = []
not_w = []
i = 0
a = 0
import time 
st = time.time()
for filename in hrefs:
    date,Type,_ = filename.split("_",2)
    if Type.upper() in pmsensors:
        a+=1
        try:
            l.append(convert_AQI(folder + filename, date))
            i+=1
            print(f"{i}/{a} processed.\r", end="")
        except Exception as e:
            not_w.append(filename)

dt = time.time() - st
logger.info(f"Processed {i} out of {a} files in {dt:.2f} seconds.")
logger.info(f"Files not processed for 2025-12-19: {not_w}")

logger.info(f"Saving results to ./data/AQI_2025-12-19.csv")
cols = ["sensor_id", "sensor_type", "location", "lat", "lon", "altitude", "date", "PM10", "PM2.5"]
ndf = pd.DataFrame(l, columns=cols)
ndf.to_csv("./data/AQI_2025-12-19.csv", index=False)

