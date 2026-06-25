#!/bin/bash
# =============================================
# 广铁机考服务平台 - 腾讯云一键部署脚本
# 适用：腾讯云轻量应用服务器 2核4G
# =============================================

set -e

echo "========================================"
echo "  🚂 广铁机考服务平台 - 一键部署"
echo "========================================"
echo ""

# 1. 更新系统
echo "📦 [1/6] 更新系统包..."
apt-get update -qq && apt-get install -y -qq git curl 2>&1 | tail -1

# 2. 安装 Python 依赖
echo "📦 [2/6] 安装 Python 依赖..."
pip install --no-cache-dir -r requirements.txt -q 2>&1 | tail -1

# 3. 验证代码完整性
echo "🔍 [3/6] 验证代码..."
python3 -c "
import sys
sys.path.insert(0, '.')
import importlib.util
spec = importlib.util.spec_from_file_location('railway_main', 'railway_main.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
routes = [r.path for r in mod.app.routes if hasattr(r, 'path')]
print(f'   ✅ 网站加载成功')
print(f'   路由: {routes}')
"

# 4. 创建 systemd 服务（开机自启 + 崩溃重启）
echo "⚙️  [4/6] 创建系统服务..."
cat > /etc/systemd/system/railway-exam.service << 'SERVICEEOF'
[Unit]
Description=广铁机考服务平台
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/project
ExecStart=/usr/bin/python3 -m uvicorn railway_main:app --host 0.0.0.0 --port 8080 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# 5. 启动服务
echo "🚀 [5/6] 启动服务..."
systemctl daemon-reload
systemctl enable railway-exam.service
systemctl restart railway-exam.service

# 6. 配置防火墙（腾讯云默认安全组，但本地也放行）
echo "🛡️  [6/6] 配置防火墙..."
ufw allow 8080/tcp 2>/dev/null || echo "   (ufw 未安装，跳过)"

echo ""
echo "========================================"
echo "  ✅ 部署完成！"
echo "========================================"
echo ""
echo "  访问地址：http://服务器IP:8080"
echo ""
echo "  题库：/exam/"
echo "  招录查询：/railway/"
echo ""
echo "  常用命令："
echo "    systemctl status railway-exam    # 查看状态"
echo "    systemctl restart railway-exam   # 重启"
echo "    journalctl -u railway-exam -f    # 查看实时日志"
echo "========================================"