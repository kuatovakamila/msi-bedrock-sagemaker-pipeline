import os, time, json
import joblib, numpy as np
from flask import Flask, request, jsonify
import boto3

# Environment variables with defaults
REGION = os.environ.get('AWS_REGION', 'us-east-1')
MODEL_PATH = os.environ.get('MODEL_PATH', '/opt/ml/model/model.pkl')
NAMESPACE = os.environ.get('NAMESPACE', 'MSI/AnomalyService')

app = Flask(__name__)

model = None
cw = boto3.client("cloudwatch", region_name=REGION)

try:
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
except Exception as e:
    bedrock = None

@app.route("/ping", methods=["GET"])
def ping():
    global model
    if model is None:
        if not os.path.exists(MODEL_PATH):
            return "Model not ready", 503
        model = joblib.load(MODEL_PATH)
    return 'ok', 200

@app.route("/invocations", methods=["POST"])
def invocations():
    global model
    if model is None:
        if not os.path.exists(MODEL_PATH):
            return "Model not ready", 503
        model = joblib.load(MODEL_PATH)
    
    payload = request.get_json(force=True)
    x = np.array(payload.get('instances', []))
    
    if len(x) == 0:
        return jsonify({"error": "No instances provided"}), 400
    
    t0 = time.time()
    pred_raw = model.predict(x)
    anomalies = (pred_raw == -1).astype(int).tolist()
    latency_ms = (time.time() - t0) * 1000

    try:
        cw.put_metric_data(
            Namespace=NAMESPACE, 
            MetricData=[
                {"MetricName": "LatencyMs", "Value": latency_ms, "Unit": "Milliseconds"},
                {"MetricName": "AnomalyRate", "Value": sum(anomalies)/max(len(anomalies), 1)}
            ]
        )
    except Exception as e:
        print("CloudWatch error:", e)

    summary = None
    if bedrock and any(anomalies):
        try:
            prompt = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 128,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Summarize in one sentence: Telemetry anomalies detected. Provide an operator-friendly note."
                            }
                        ]
                    }
                ]
            }
            resp = bedrock.invoke_model(
                modelId=os.environ.get('BEDROCK_MODEL', 'anthropic.claude-3-5-haiku-20241022-v1:0'),
                body=json.dumps(prompt)
            )
            body = json.loads(resp.get('body').read())
            summary = body.get('content', [{}])[0].get('text')
        except Exception as e:
            summary = f'bedrock error: {e}'
    
    return jsonify({
        "anomalies": anomalies, 
        "latency_ms": latency_ms, 
        "summary": summary
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)