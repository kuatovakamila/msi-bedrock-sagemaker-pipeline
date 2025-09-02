# MSI Bedrock + SageMaker Mini-Pipeline


**AWS:** **SageMaker**, **ECR**, **S3**, **CloudWatch**, **IAM**, **(optional) Bedrock**
**ML:** scikit-learn, Optuna, Pandas, NumPy
**Runtime:** Docker BYOC, Flask/Gunicorn


## Architecture
```mermaid
flowchart LR
subgraph Dev[GitHub Actions]
A1[Generate data & train (sklearn+Optuna)] --> A2[Upload model.tar.gz to S3]
A3[Build Docker image] --> A4[Push to ECR]
A5[Terraform apply] -->|create| SM1[SageMaker Model]
end
SM1 --> SM2[Endpoint Config] --> SM3[Endpoint]
C1[Client / load test] -->|/invocations| SM3
SM3 -->|put_metric_data| CW[(CloudWatch)]
SM3 -->|if alert| BR[(Bedrock summarization)]