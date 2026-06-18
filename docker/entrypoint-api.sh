#!/bin/sh
set -e
mkdir -p /app/var
python -m app.db.init_db
if [ -f /app/data/production_data.csv ] && [ "${AUTO_SEED:-0}" = "1" ]; then
    python -m app.features.ingestion.seed /app/data/production_data.csv
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
