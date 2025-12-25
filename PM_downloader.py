import time
import requests
import re
import logging
import os
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

folder = f"https://archive.sensor.community/csv_per_month/"
local = "../s3/"

start = date(2025, 1, 1)
end = date(2025, 11, 1)
current = start
while current < end:
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

    html = response.text
    pattern = re.compile(r'<a href="([^"]+\.zip)"', re.IGNORECASE)
    hrefs = pattern.findall(html)
    not_w = []
    i = 0
    a = 0
    st = time.time()
    logger.info(f"Processing files for month starts on {current} ...")
    for filename in hrefs:
        date_,Typezip = filename.split("_",1)
        Type,_ = Typezip.split(".",1)
        if Type.upper() in pmsensors:
            a+=1
            local_path = local + f"{yr}-{mo}/" + filename
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            for rt in range(5):
                try:
                    with requests.get(folder + f"{yr}-{mo}/"+ filename, stream=True) as r:
                        r.raise_for_status()
                        total = int(r.headers.get("Content-Length", 0))
                        downloaded = 0
                        with open(local_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=1024 * 1024*8):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                    i+=1 
                    break               
                except Exception as e:
                    logger.warning(f"Failed to download {local_path} for {rt}th times: {e}")
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    if rt == 4:
                        not_w.append(filename)
    dt = time.time() - st
    logger.info(f"\nProcessed {i} out of {a} files in {dt:.2f} seconds. for date {current}")
    logger.info(f"Files not processed for {current}: {not_w}")
    # Next month
    if current.month == 12:
            current = date(current.year + 1, 1, 1)
    else:
        current = date(current.year, current.month + 1, 1)