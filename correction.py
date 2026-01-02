import pandas as pd
from pathlib import Path
local_data_folder = r"C:\Users\Shenghui\Documents\GitHub\MSc_CC_AirQuality\data\s3"
for folder in Path(local_data_folder).iterdir():
    if folder.is_dir():
        Fname = folder.name 
        date = Fname.split('=')[1]
        pq_file = list(folder.glob('*.parquet'))[0]
        df = pd.read_parquet(pq_file)
        df.insert(0, 'date', date)
        df.to_parquet(pq_file, index=False, engine='pyarrow', compression='snappy')