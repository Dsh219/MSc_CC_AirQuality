# MSc_CC_AirQuality
Course work for cloud computing at Cranfield: handle request on air quality from hourly to daily.

Live data is from:
  Averaged data from last hour for each sensor:
    https://data.sensor.community/static/v2/data.1h.json
  Daily archived data for each sensor:
    https://archive.sensor.community


# Directory overview:
  1. creds/ is where AWS lab session credentials goes
  2. data/s3/ is where archive monthly data from 2015-10-01 to 2025-11-30
  3. frontend/ has index.html and locations.json for frontend UI
  4. load_test/ has all K6 load test scripts
  5. zips/ holds all lambda function zipped files
  6. lambda function scripts are stored in the working directory with prefix lambda_
  7. setup.py is used to setup entire application by using boto3
            |---> Only change the S3 buckets
  8. PM_downloader.py can be used to download monthly zip data, only change the start date and end date.
  9. local_AQI_Mzip.py can be used to extract the zip and convert it to parquet files.
            |---> pyarrow should be installed 


# Load test is done on t5.large EC2 instance running Ubuntu:
  volume choices 500 -> 2k -> 10k

Access the instance:  
  ssh -i labsuser.pem ubuntu@public-ip

first install k6:
  sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
  echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
  sudo apt-get update
  sudo apt-get install k6

then use cmd to transfer script to the target:
  scp -i ./labsuser.pem ./test.js ubuntu@100.27.7.39:~/

then excute the script:
  k6 run test.js