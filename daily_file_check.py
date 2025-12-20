# -*- coding: utf-8 -*-

import pandas as pd
import os
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

daily_file = "./data/AQI_2025-12-19.csv"
df = pd.read_csv(daily_file,sep=",")

is_unique = not df.duplicated(subset=["lat", "lon"]).any()
logger.info(f"Checking if lat and lon are unique in {daily_file}")
logger.info(f"lat and lon are unique: {is_unique}")

dup_keys = df.groupby(["lat", "lon"]).size()
dup_keys = dup_keys[dup_keys > 1]
if not is_unique:
    logger.info("Duplicate entries found for the following lat and lon combinations:")
    logger.info(dup_keys)