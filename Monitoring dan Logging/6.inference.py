import requests
import json
import time
import logging
import pandas as pd

# Setup logging
logging.basicConfig(filename="api_logs.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

API_URL = "http://127.0.0.1:8000/invocations"

# Load data dan hapus label (kolom target)
df = pd.read_csv("personality.csv")
df = df.drop(columns=["Personality"])

# Ambil beberapa sample (misal 3 baris) untuk inference
sample = df.sample(3, random_state=42)

# Siapkan payload
input_data = {
    "dataframe_split": {
        "columns": sample.columns.tolist(),
        "data": sample.values.tolist()
    }
}

headers = {"Content-Type": "application/json"}
payload = json.dumps(input_data)

start_time = time.time()

try:
    response = requests.post(API_URL, headers=headers, data=payload)
    response_time = time.time() - start_time

    if response.status_code == 200:
        prediction = response.json()
        logging.info(f"Prediction successful: {prediction} in {response_time:.4f} sec")
        print(f"Prediction: {prediction}")
        print(f"Response Time: {response_time:.4f} sec")
    else:
        logging.error(f"Error {response.status_code}: {response.text}")
        print(f"Error {response.status_code}: {response.text}")

except Exception as e:
    logging.error(f"Exception: {str(e)}")
    print(f"Terjadi kesalahan: {str(e)}")
