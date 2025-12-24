import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
import re

folder = f"https://archive.sensor.community/2025-12-19/"
local = "../s3/"
for t in range(5):
    try:
        response = requests.get(folder)
        response.raise_for_status()  # raises error if request failed
        break
    except Exception as e:
        time.sleep(2)
        if t == 4:  
            skip = True

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
        local_path = local + "2025-12-19/" + filename
       # os.makedirs(local_path, exist_ok=True)
        try:
            response = requests.get(folder + filename, timeout=120)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            i+=1
            print(f" done: {i}/{a} files processed\r", end='', flush=True)
        except Exception as e:
            not_w.append(filename)

current = "2015-12-19"
dt = time.time() - st
print(f"\nProcessed {i} out of {a} files in {dt:.2f} seconds. for date {current}")
print(f"Files not processed for {current}: {not_w}")
print(f" done: {i}/{a} files processed in {dt:.2f} seconds.\r", end='', flush=True)
