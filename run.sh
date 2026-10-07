#!/usr/bin/env bash
# Start Blue Since Boyhood in the background (idempotent). Rebuilds data/chelsea.json from data/raw/ first (no network).
cd "$(dirname "$0")"
PORT=${CHELSEA_TM_PORT:-4247}
python3 build_data.py >/dev/null
if curl -fs "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
  echo "Blue Since Boyhood already running: http://127.0.0.1:$PORT"; exit 0
fi
setsid nohup python3 server.py > data/server.log 2>&1 < /dev/null &
sleep 1
echo "Blue Since Boyhood started (pid $!): http://127.0.0.1:$PORT"
