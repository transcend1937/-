#!/bin/bash
# ============================================
# 广铁机考模拟题库 - 一键启动脚本
# 用法: bash start_exam.sh
# ============================================

cd /workspace/projects

echo "========================================"
echo "  广铁机考模拟题库 启动中..."
echo "========================================"

# 1. 设置环境变量
export PYTHONPATH=/workspace/projects/src:$PYTHONPATH

# 2. 杀掉旧的进程
OLD_PID=$(lsof -t -i:5000 2>/dev/null)
if [ -n "$OLD_PID" ]; then
    echo "[1/3] 关闭旧服务 (PID: $OLD_PID)..."
    kill -9 $OLD_PID 2>/dev/null
    sleep 1
else
    echo "[1/3] 端口 5000 空闲"
fi

# 3. 启动新服务
echo "[2/3] 启动 uvicorn 服务..."
nohup uvicorn src.exam.app:app --host 0.0.0.0 --port 5000 > /tmp/exam_server.log 2>&1 &
sleep 2

# 4. 验证启动
echo "[3/3] 验证服务状态..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/exam/ | grep -q 200; then
    echo ""
    echo "========================================"
    echo "  ✅ 启动成功！"
    echo "========================================"
    echo ""
    echo "  本地访问:  http://localhost:5000/exam/"
    echo ""
    echo "  常用命令:"
    echo "    bash start_exam.sh              # 启动/重启"
    echo "    tail -f /tmp/exam_server.log    # 查看实时日志"
    echo "    lsof -i:5000                    # 查看端口占用"
    echo ""
else
    echo "  ⚠️  服务可能未完全启动，等待 3 秒重试..."
    sleep 3
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/exam/ | grep -q 200; then
        echo "  ✅ 启动成功！"
        echo "  访问: http://localhost:5000/exam/"
    else
        echo "  ❌ 启动失败，请查看日志: tail -30 /tmp/exam_server.log"
        echo ""
        echo "  手动启动:"
        echo "    cd /workspace/projects"
        echo "    PYTHONPATH=/workspace/projects/src nohup uvicorn src.exam.app:app --host 0.0.0.0 --port 5000 &"
    fi
fi