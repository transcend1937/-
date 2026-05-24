#!/bin/bash
# ============================================
# 广铁机考模拟题库 - 启动脚本
# 用法: bash start_exam.sh
# ============================================

cd "$(dirname "$0")"

echo "========================================"
echo "  广铁机考模拟题库 启动中..."
echo "========================================"

# 1. 检查 supervisor 是否在运行
SUPERVISOR_RUNNING=false
supervisorctl status exam_app &>/dev/null && SUPERVISOR_RUNNING=true

if [ "$SUPERVISOR_RUNNING" = true ]; then
    # 重启服务
    echo "[1/2] supervisor 管理中，重启服务..."
    supervisorctl restart exam_app
    sleep 2
else
    # 启动 supervisor
    echo "[1/3] 启动 supervisor..."
    supervisord -c /etc/supervisor/supervisord.conf 2>/dev/null
    sleep 1
    supervisorctl reread &>/dev/null
    supervisorctl update &>/dev/null
    sleep 2
fi

# 检查状态
if supervisorctl status exam_app | grep -q RUNNING; then
    echo ""
    echo "✅ 启动成功！"
    echo ""
    echo "  本地访问:  http://localhost:5000/exam/"
    echo ""
    echo "  管理命令:"
    echo "    supervisorctl status exam_app        # 查看状态"
    echo "    supervisorctl restart exam_app       # 重启服务"
    echo "    supervisorctl stop exam_app          # 停止服务"
    echo "    supervisorctl tail exam_app          # 查看日志"
    echo ""
else
    echo "❌ 启动失败，查看日志: tail -20 /tmp/exam_app_err.log"
    echo ""
    echo "  备用启动:  cd /workspace/projects && nohup uvicorn src.exam.app:app --host 0.0.0.0 --port 5000 &"
fi