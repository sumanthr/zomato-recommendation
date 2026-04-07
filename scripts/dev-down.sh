#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"

stop_pid_file() {
  local name="$1"
  local pid_file="$2"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      echo "Stopped $name (pid $pid)"
    else
      echo "$name already stopped"
    fi
    rm -f "$pid_file"
  else
    echo "$name pid file missing"
  fi
}

stop_pid_file "backend" "$RUN_DIR/backend.pid"
stop_pid_file "frontend" "$RUN_DIR/frontend.pid"

if lsof -i :8001 >/dev/null 2>&1; then
  lsof -t -i :8001 | xargs kill -9 2>/dev/null || true
  echo "Stopped process on port 8001"
fi
if lsof -i :5174 >/dev/null 2>&1; then
  lsof -t -i :5174 | xargs kill -9 2>/dev/null || true
  echo "Stopped process on port 5174"
fi
