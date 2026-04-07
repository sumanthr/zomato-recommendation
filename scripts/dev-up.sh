#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
mkdir -p "$RUN_DIR"

cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -r requirements.txt >/dev/null
if [[ "${FORCE_SAMPLE_DATA:-false}" == "true" ]]; then
  .venv/bin/python -m src.phases.phase_7.bootstrap_sample_data >/dev/null
elif [[ ! -f "$ROOT_DIR/data/processed/restaurants.parquet" ]]; then
  .venv/bin/python -m src.phases.phase_7.bootstrap_sample_data >/dev/null
fi

if [[ ! -d ".nodeenv" ]]; then
  .venv/bin/python -m pip install nodeenv >/dev/null
  .venv/bin/nodeenv -n 20.11.1 .nodeenv >/dev/null
fi

source "$ROOT_DIR/.nodeenv/bin/activate"
cd "$ROOT_DIR/src/phases/phase_5/frontend"
npm install >/dev/null
cd "$ROOT_DIR"

BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"
BACKEND_PORT=8001
FRONTEND_PORT=5174

if lsof -i :"$BACKEND_PORT" >/dev/null 2>&1; then
  lsof -t -i :"$BACKEND_PORT" | xargs kill -9 2>/dev/null || true
fi
pkill -f "uvicorn src.phases.phase_4.api:app" 2>/dev/null || true

if lsof -i :"$FRONTEND_PORT" >/dev/null 2>&1; then
  lsof -t -i :"$FRONTEND_PORT" | xargs kill -9 2>/dev/null || true
fi
pkill -f "vite --host 127.0.0.1 --port $FRONTEND_PORT" 2>/dev/null || true

if [[ -f "$RUN_DIR/backend.pid" ]] && kill -0 "$(cat "$RUN_DIR/backend.pid")" 2>/dev/null; then
  echo "Backend already running (pid $(cat "$RUN_DIR/backend.pid"))"
else
  nohup "$ROOT_DIR/.venv/bin/python" -m uvicorn src.phases.phase_4.api:app --host 127.0.0.1 --port "$BACKEND_PORT" >"$BACKEND_LOG" 2>&1 &
  echo $! > "$RUN_DIR/backend.pid"
fi

if [[ -f "$RUN_DIR/frontend.pid" ]] && kill -0 "$(cat "$RUN_DIR/frontend.pid")" 2>/dev/null; then
  echo "Frontend already running (pid $(cat "$RUN_DIR/frontend.pid"))"
else
  nohup bash -lc "source \"$ROOT_DIR/.nodeenv/bin/activate\" && cd \"$ROOT_DIR/src/phases/phase_5/frontend\" && VITE_API_BASE_URL=http://127.0.0.1:$BACKEND_PORT npm run dev -- --host 127.0.0.1 --port $FRONTEND_PORT --strictPort" >"$FRONTEND_LOG" 2>&1 &
  echo $! > "$RUN_DIR/frontend.pid"
fi

echo "Backend:  http://127.0.0.1:$BACKEND_PORT"
echo "Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "Logs: $RUN_DIR/backend.log and $RUN_DIR/frontend.log"
