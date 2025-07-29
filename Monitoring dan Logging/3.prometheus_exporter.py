from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST, ProcessCollector
import time
import psutil
import requests
import logging
import random

app = Flask(__name__)

# Logging
logging.basicConfig(filename="model_monitoring", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Prometheus default process metrics
ProcessCollector()

# ----- Custom Prometheus Metrics -----
INFERENCE_TIME = Summary('model_inference_duration_seconds', 'Duration of model inference')
REQUEST_COUNT = Counter('model_request_total', 'Total number of model prediction requests')
REQUEST_LATENCY = Histogram('model_request_latency_seconds', 'Latency of model requests')
F1_SCORE = Gauge('model_f1_score', 'Current F1 Score of the ML model')
CPU_USAGE = Gauge('system_cpu_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_mb', 'Memory usage in megabytes')

# ----- Endpoint for Prometheus to scrape -----
@app.route('/metrics', methods=['GET'])
def metrics():
    CPU_USAGE.set(psutil.cpu_percent(interval=0.5))
    MEMORY_USAGE.set(psutil.virtual_memory().used / 1024 / 1024)
    # Simulasi F1 Score antara 0.7 - 0.99
    F1_SCORE.set(random.uniform(0.7, 0.99))  
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# ----- Prediction Proxy Endpoint -----
@app.route('/predict', methods=['POST'])
def predict():
    REQUEST_COUNT.inc()
    start_time = time.time()

    try:
        data = request.get_json()
        # Kirim ke model backend
        response = requests.post("http://localhost:5005/invocations", json=data, timeout=5)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        logging.error(f"Prediction failed: {e}")
        return jsonify({"error": "Inference failed or backend unreachable"}), 500

    duration = time.time() - start_time
    INFERENCE_TIME.observe(duration)
    REQUEST_LATENCY.observe(duration)

    return jsonify(result)

# ----- Run Server -----
if __name__ == '__main__':
    print(" Monitoring Exporter is running at http://localhost:8001")
    app.run(host='127.0.0.1', port=8001)
