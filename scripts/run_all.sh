#!/bin/bash

# -------------------------------
# 1️⃣ 获取脚本目录和项目根
# -------------------------------
SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")

# -------------------------------
# 2️⃣ 停止旧的后端和前端进程
# -------------------------------
echo "Stopping old backend and frontend if running..."

# 后端 8000
BACKEND_PID=$(lsof -ti:8000)
if [ -n "$BACKEND_PID" ]; then
    echo "Killing old backend process $BACKEND_PID"
    kill -9 $BACKEND_PID
fi

# 前端 5173
FRONTEND_PID=$(lsof -ti:5173)
if [ -n "$FRONTEND_PID" ]; then
    echo "Killing old frontend process $FRONTEND_PID"
    kill -9 $FRONTEND_PID
fi

# -------------------------------
# 3️⃣ 启动后端
# -------------------------------
echo "Starting backend..."
cd "$PROJECT_ROOT/backend" || exit
export PYTHONPATH=$PROJECT_ROOT/backend
nohup uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &

# 等待后端启动
sleep 3

# -------------------------------
# 4️⃣ 启动前端
# -------------------------------
echo "Starting frontend..."
cd "$PROJECT_ROOT/frontend" || exit
npm install
nohup npm run dev > frontend.log 2>&1 &

# -------------------------------
# 5️⃣ 输出访问信息
# -------------------------------
echo "All services started!"
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000/multi-agent-task?q=iphone"