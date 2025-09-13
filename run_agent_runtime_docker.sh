#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[run] Checking prerequisites..."
command -v docker >/dev/null || { echo "[error] docker not found in PATH" >&2; exit 1; }
if ! docker compose version >/dev/null 2>&1; then
  echo "[error] docker compose is required (Docker Desktop 2.20+)." >&2
  exit 1
fi
command -v curl >/dev/null || { echo "[error] curl not found" >&2; exit 1; }

echo "[run] Bringing up agent-runtime via Docker Compose..."
docker compose down -v --remove-orphans || true
docker compose build --no-cache
docker compose up -d

echo "[run] Waiting for backend on :8000..."
for i in $(seq 1 90); do
  if curl -sf http://127.0.0.1:8000/docs > /dev/null 2>&1; then
    echo "[ok] Backend is up"
    break
  fi
  sleep 1
  if [ "$i" -eq 90 ]; then
    echo "[error] Backend failed to start; last logs:" >&2
    docker compose logs --tail=200 >&2 || true
    exit 1
  fi
done

echo "[run] Tools status:"
curl -sf http://127.0.0.1:8000/v1/tools/status | sed -e 's/},{/},\n{/g' || true

if ! command -v jq >/dev/null 2>&1; then
  echo "[warn] jq not found; skipping E2E task. Install jq to run full test." >&2
  exit 0
fi

echo "[run] Submitting E2E task..."
TASK_ID=$(curl -sf -H 'Content-Type: application/json' \
  -d '{"prompt":"Create a file src/agent_runtime/sample_data/container_test.txt with content: AGENT OK"}' \
  http://127.0.0.1:8000/v1/tasks | jq -r .task_id)
echo "[ok] TASK_ID=$TASK_ID"

echo "[run] Waiting for plan (awaiting_approval)..."
for i in $(seq 1 120); do
  STATUS_JSON=$(curl -sf http://127.0.0.1:8000/v1/tasks/$TASK_ID)
  STATUS=$(echo "$STATUS_JSON" | jq -r .status)
  printf "[plan] status=%s\r" "$STATUS"
  if [ "$STATUS" = "awaiting_approval" ]; then
    echo
    echo "[plan] Plan:" && echo "$STATUS_JSON" | jq -r .plan
    break
  fi
  if [ "$STATUS" = "failed" ]; then
    echo
    echo "$STATUS_JSON" | jq . >&2
    exit 1
  fi
  sleep 1
  if [ "$i" -eq 120 ]; then
    echo
    echo "[error] Timed out waiting for plan" >&2
    exit 1
  fi
done

echo "[run] Approving plan..."
curl -sf -X POST http://127.0.0.1:8000/v1/tasks/$TASK_ID/approve >/dev/null
echo "[ok] Approved"

echo "[run] Waiting for completion..."
for i in $(seq 1 180); do
  STATUS_JSON=$(curl -sf http://127.0.0.1:8000/v1/tasks/$TASK_ID)
  STATUS=$(echo "$STATUS_JSON" | jq -r .status)
  printf "[exec] status=%s\r" "$STATUS"
  if [ "$STATUS" = "completed" ]; then
    echo
    echo "[result]" && echo "$STATUS_JSON" | jq -r .result
    break
  fi
  if [ "$STATUS" = "failed" ]; then
    echo
    echo "$STATUS_JSON" | jq . >&2
    exit 1
  fi
  sleep 1
  if [ "$i" -eq 180 ]; then
    echo
    echo "[error] Timed out waiting for completion" >&2
    exit 1
  fi
done

echo "[run] Verifying file inside container..."
CID=$(docker compose ps -q agent-runtime)
docker exec "$CID" sh -lc 'ls -l /app/src/agent_runtime/sample_data && echo "---" && cat /app/src/agent_runtime/sample_data/container_test.txt'

echo "[done] Agent Runtime E2E finished successfully."

