import pandas as pd
from pathlib import Path
local_data_folder = r"C:\Users\Shenghui\Documents\GitHub\parquet"
local_data_folder =r"C:\Users\Shenghui\Documents\GitHub\MSc_CC_AirQuality\data\s3"

'''
error=[]
for folder in Path(local_data_folder).iterdir():
    if folder.is_dir():
        try:
            Fname = folder.name 
            date = Fname.split('=')[1]
            pq_file = list(folder.glob('*.parquet'))[0]
            df = pd.read_parquet(pq_file)
            df.insert(0, 'date', date)
            df.to_parquet(pq_file, index=False, engine='pyarrow', compression='snappy')
            print(f"\r{Fname}", end='', flush=True)
        except Exception as e:
            error.append((folder, str(e)))
            print(f"\nError processing folder {folder}: {e}")
if error:
    with open("correction_error.log", "w") as f:
        for folder, err in error:
            f.write(f"Folder: {folder}, Error: {err}\n")
'''

error=[]
for folder in Path(local_data_folder).iterdir():
    if folder.is_dir():
        try:
            Fname = folder.name 
            date = Fname.split('=')[1]
            pq_file = list(folder.glob('*.parquet'))[0]
            df = pd.read_parquet(pq_file)
            #df.insert(0, 'date', date)
            df =df.rename(columns={'date':'rdate'})
            df['rdate'] = df['rdate'].astype(str)
            df['lat'] = df['lat'].astype(str)     # lat as string
            df['lon'] = df['lon'].astype(str)     # lon as string
            df['AQI'] = df['AQI'].fillna(0).astype(int)  # AQI as integer, replace NaN with 0
            df.to_parquet(pq_file, index=False, engine='pyarrow', compression='snappy')
            print(f"\r{Fname}", end='', flush=True)
        except Exception as e:
            error.append((folder, str(e)))
            print(f"\nError processing folder {folder}: {e}")
if error:
    with open("correction_error.log", "w") as f:
        for folder, err in error:
            f.write(f"Folder: {folder}, Error: {err}\n")