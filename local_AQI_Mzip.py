import pandas as pd
import glob
import os
import time
from datetime import date, timedelta
import zipfile
import shutil
st = time.time()
# P1: PM10, P2: PM2.5
PM10_bins = [0, 17, 34, 51, 59, 67, 76, 84, 92, 101, float('inf')]
PM10_labels = [1,2,3,4,5,6,7,8,9,10]
PM25_bins = [0,12,24,36,42,48,54,59,65,71,float('inf')]
PM25_labels = [1,2,3,4,5,6,7,8,9,10]
valid_cols = ['sensor_id', 'sensor_type', 'location', 'lat', 'lon', 'timestamp', 'P1', 'P2']

def process_large_csv_to_parquet(input_folder:str, output_folder:str, chunk_size:int=500_000) -> None:

    csv_files = glob.glob(os.path.join(input_folder, "*.csv")) # unzipped csv files in a month folder
    chunk_results = []
    for file_path in csv_files:
        with pd.read_csv(
            file_path, 
            sep=';',              
            chunksize=chunk_size, 
            usecols=valid_cols,
            dtype={
                'lat': 'float32', 
                'lon': 'float32',
                'P1': 'string',  
                'P2': 'string'
            }  # Read P1 and P2 as string first to handle "" or "None"
        ) as reader:
            for i, chunk in enumerate(reader):
                # Timestamp to Date  == 'YYY-MM-DDTHH:MM:SSZ' -> 'YYYY-MM-DD'
                chunk['date'] = chunk['timestamp'].str.slice(0, 10)
                chunk['P1'] = pd.to_numeric(chunk['P1'], errors='coerce')
                chunk['P2'] = pd.to_numeric(chunk['P2'], errors='coerce')
                # Group the chunk by <date, lat, lon>  and get sum and count
                grouped = chunk.groupby(['date', 'lat', 'lon'])[['P1', 'P2']].agg(['sum', 'count'])
                # Flatten columns from groupby to single row columns(headers) => P1_sum, P1_count, P2_sum, P2_count
                grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
                grouped = grouped.reset_index()
                # Store this small aggregated dataframe
                chunk_results.append(grouped)

    if not chunk_results:
        raise ValueError("No data found.")

    # Combine all aggregated dataframes
    full_df = pd.concat(chunk_results, ignore_index=True)
    
    # Group again to sum up the partial sums and counts
    final_group = full_df.groupby(['date', 'lat', 'lon']).sum().reset_index()
    
    df = pd.to_datetime(final_group['date'],errors="coerce", format="%Y-%m-%d") # covert normal yyyy-mm-dd to datetime
    mask = df.isna() # get the mask for invalid dates (unix timestamps)
    if mask.any():
        numeric_dates = pd.to_numeric(final_group.loc[mask,'date'],errors="coerce")
        df.loc[mask] = pd.to_datetime(numeric_dates,unit='s',errors="coerce")
    final_group['date'] = df.dt.date
    # Calculate the raw means first (vectorized division)
    p1_mean = final_group['P1_sum'] / final_group['P1_count']
    p2_mean = final_group['P2_sum'] / final_group['P2_count']
    
    # Convert PM readings to AQI scores using pd.cut for vectorized binning
    # float conversion is for safe conversion on NaN results
    final_group['P1_score'] = pd.cut(p1_mean, bins=PM10_bins, labels=PM10_labels).astype(float)
    final_group['P2_score'] = pd.cut(p2_mean, bins=PM25_bins, labels=PM25_labels).astype(float)

    # Set AQI --- Max of the two scores
    final_group['AQI'] = final_group[['P1_score', 'P2_score']].max(axis=1)

    # Keep only relevant columns
    result_df = final_group[['date', 'lat', 'lon', 'AQI']]
    result_df.to_parquet(output_folder, index=False, engine='pyarrow', 
                         compression='snappy', partition_cols=['date'])
    print(f"Converted all CSVs in {input_folder} to Parquet at {output_folder}")

def unzip_files_in_folder(folder_path: str, output_dir: str | None = None) -> None:
    # Unzip all zip files in the given folder to the output directory
    if output_dir is None:
        output_dir = folder_path

    os.makedirs(output_dir, exist_ok=True)
    # Find all zip files in the folder
    zip_files = glob.glob(os.path.join(folder_path, "*.zip"))

    for zip_file in zip_files:
        with zipfile.ZipFile(zip_file, "r") as z:
            for member in z.infolist():
                if member.is_dir():
                    continue
                # Get the filename
                filename = os.path.basename(member.filename)
                if not filename:
                    continue
                # Construct the target path
                target_path = os.path.join(output_dir, filename)
                # Extract file content by chunks to avoid memory issues
                with z.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024 * 500)
    print(f"Unzipped files in {folder_path}")

start = date(2020, 7, 1)
end = date(2020, 12, 20)
current = start
of = r"C:\Users\Shenghui\Documents\GitHub\parquet" + "\\"
#folder = r"C:\Users\Shenghui\Documents\GitHub\s3"
folder = r"E:\zips"
#folder = r"D:\s3_to_be_done"

FromFolder = lambda mF, mo, yr : mF +  f"\{yr}-{mo:02d}" + "\\"

while current <= end:
    current = date(current.year, current.month, 1)
    
    #unzip_files_in_folder(FromFolder(folder, current.month, current.year))
    process_large_csv_to_parquet(FromFolder(folder, current.month, current.year), of)
    current += timedelta(days=31)




print(f"Total time taken: {time.time() - st} seconds")
