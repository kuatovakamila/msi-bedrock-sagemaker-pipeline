FROM python:3.11-slim
WORKDIR /opt/program

# (optional but useful) certs/tzdata for AWS SDKs & HTTPS
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates tzdata && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /opt/program/entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# SageMaker compatibility: understands "serve"
ENTRYPOINT ["/opt/program/entrypoint.sh"]
CMD ["serve"]
