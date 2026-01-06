#!/bin/bash
# Start MLflow UI from project root
cd "$(dirname "$0")"
echo "Starting MLflow UI..."
echo "MLruns directory: $(pwd)/mlruns"
if [ ! -d "mlruns" ]; then
    echo "WARNING: mlruns directory does not exist yet."
    echo "Run your training notebook first to create experiments."
    echo ""
fi
mlflow ui --host 127.0.0.1 --port 5000

