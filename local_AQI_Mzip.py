import glob
import pyarrow as pa
import pyarrow.csv as pv
import pyarrow.parquet as pq
import pyarrow.compute as pc
from datetime import date, timedelta



folder = r"C:\Users\Shenghui\Documents\GitHub\s3\2025-01"
csv_files = glob.glob(f"{folder}/*.csv")
parquet_path = "output.parquet"

writer = None

current_date = date(2025,1,1)

while current_date < date(2025,2,1):
    for csv_file in csv_files:
        print(f"Processing {csv_file}")

        reader = pv.open_csv(
            csv_file,
            read_options=pv.ReadOptions(
                block_size=64 * 1024 * 1024  # 64 MB
            )
        )

        for batch in reader:
            table = pa.Table.from_batches([batch])

            



            if writer is None:
                writer = pq.ParquetWriter(
                    parquet_path,
                    table.schema,
                    compression="snappy"
                )

            writer.write_table(table)
            
    current_date += timedelta(days=1)
if writer:
    writer.close()