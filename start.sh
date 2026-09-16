#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-/runpod-volume/models/llm/qwen38-hauhau/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q6_K_P.gguf}"
LLAMA_HOST="${LLAMA_HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"

if [ ! -f "$MODEL_PATH" ]; then
  echo "ERROR: Model not found at $MODEL_PATH"
  find /runpod-volume -maxdepth 4 -type f 2>/dev/null | head -100 || true
  exit 1
fi

/app/llama-server \
  -m "$MODEL_PATH" \
  --jinja \
  --reasoning off \
  -c 65536 \
  -np 1 \
  -ctk q8_0 \
  -ctv q8_0 \
  -ngl 999 \
  --temp 0.3 \
  --top-p 0.9 \
  --top-k 20 \
  --min-p 0 \
  --presence-penalty 0 \
  --repeat-penalty 1.05 \
  --host "$LLAMA_HOST" \
  --port "$LLAMA_PORT" \
  > /tmp/llama-server.log 2>&1 &

LLAMA_PID=$!
trap 'kill "$LLAMA_PID" 2>/dev/null || true' EXIT INT TERM

READY=0
for i in $(seq 1 300); do
  if ! kill -0 "$LLAMA_PID" 2>/dev/null; then
    echo "ERROR: llama-server exited while loading"
    tail -n 200 /tmp/llama-server.log || true
    exit 1
  fi

  CODE=$(curl -s -o /tmp/llama-health.json -w "%{http_code}" "http://${LLAMA_HOST}:${LLAMA_PORT}/health" || true)
  if [ "$CODE" = "200" ]; then
    READY=1
    break
  fi
  sleep 2
done

if [ "$READY" != "1" ]; then
  echo "ERROR: llama-server did not become ready"
  tail -n 200 /tmp/llama-server.log || true
  exit 1
fi

exec /opt/venv/bin/python -u /app/handler.py
