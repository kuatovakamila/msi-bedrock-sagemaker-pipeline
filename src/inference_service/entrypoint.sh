#!/usr/bin/env bash
set -euo pipefail

# SageMaker passes "serve" on startup.
if [[ "${1:-}" == "serve" || -z "${1:-}" ]]; then
  exec gunicorn -w 2 -b 0.0.0.0:8080 wsgi:application
else
  exec "$@"
fi
