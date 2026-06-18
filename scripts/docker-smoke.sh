#!/bin/bash
set -e

docker compose down -v 2>/dev/null || true
docker compose build
docker compose up -d

echo "=== Waiting for services to be healthy (15s) ==="
sleep 15

echo "=== API health ==="
curl -fs http://localhost:8000/health
echo
echo "OK"

echo "=== Web index ==="
curl -fs http://localhost:3000/ -o /dev/null
echo "OK"

echo "=== API logs (last 20) ==="
docker compose logs api | tail -20

echo "=== Web logs (last 20) ==="
docker compose logs web | tail -20

echo "=== Smoke test passed, cleaning up ==="
docker compose down
