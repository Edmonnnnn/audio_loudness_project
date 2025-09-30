#!/usr/bin/env bash
set -euo pipefail
cd /home/edmon/sites/lufs.bots-ai.net
export PYTHONPATH=/home/edmon/sites/lufs.bots-ai.net
source backend/venv/bin/activate
pkill -f "uvicorn.*8211" || true
mkdir -p logs
nohup python -m uvicorn backend.main:app \
  --host 0.0.0.0 --port 8211 --log-level info \
  > logs/uvicorn.out 2>&1 &
