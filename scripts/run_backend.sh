#!/bin/bash

# 获取脚本所在目录，保证路径正确
SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")

# 后端 8000
BACKEND_PID=$(lsof -ti:8000)
if [ -n "$BACKEND_PID" ]; then
    echo "Killing old backend process $BACKEND_PID"
    kill -9 $BACKEND_PID
fi

echo "Starting backend..."
cd "$PROJECT_ROOT/backend" || exit
export PYTHONPATH=$PROJECT_ROOT/backend:$PYTHONPATH
python3 -m uvicorn app.main:app --reload --port 8000