# 🚂 广铁机考服务平台 — 腾讯云部署教程

> 包含：题库练习 + 铁路局招录数据查询
> 适用：2核4G 轻量应用服务器，可扛 1000+ 人同时访问

---

## 第一步：购买腾讯云服务器

1. 打开 👉 https://curl.qcloud.com/vYwHZpDi （轻量应用服务器）
2. 选择配置：

| 配置项 | 选择 |
|---|---|
| 地域 | 离你最近的城市（如广州/上海/北京） |
| 镜像 | **Ubuntu 22.04** |
| 套餐 | **2核4G / 8Mbps / 1200GB月流量** |
| 时长 | **6个月**（半年约 ¥228） |

3. 确认订单 → 支付
4. 购买成功后，记录 **公网 IP**

---

## 第二步：连接服务器

打开终端（Windows 用 PowerShell / Mac 用 Terminal）：

```bash
ssh root@你的服务器IP
```

输入密码（购买时设置的），登录成功。

---

## 第三步：一键部署

登录服务器后，依次执行：

```bash
# 1. 拉取代码
git clone https://github.com/transcend1937/-.git /root/project
cd /root/project

# 2. 给脚本执行权限
chmod +x deploy.sh

# 3. 一键部署
./deploy.sh
```

等待执行完成（约 1-2 分钟），看到 `✅ 部署完成！` 即成功。

---

## 第四步：访问验证

浏览器打开：

```
http://你的服务器IP:8080
```

| 功能 | 地址 |
|---|---|
| 🏠 首页 | `http://IP:8080/` |
| 📝 题库练习 | `http://IP:8080/exam/` |
| 📊 招录查询 | `http://IP:8080/railway/` |

---

## 第五步：配置域名和 HTTPS（推荐）

### 配置域名

1. 买域名（阿里云/腾讯云/百度云 都有，`.cn` 域名约 ¥30/年）
2. 腾讯云轻量控制台 → 域名管理 → 添加域名解析 A 记录 → 指向服务器 IP

### 配置 HTTPS（免费）

```bash
# 安装 Nginx 反向代理 + SSL
apt-get install -y nginx certbot python3-certbot-nginx

# 配置代理
cat > /etc/nginx/sites-enabled/railway.conf << 'EOF'
server {
    listen 80;
    server_name 你的域名.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# 申请 SSL 证书
certbot --nginx -d 你的域名.com

# 重启
systemctl restart nginx
```

---

## 常用运维命令

```bash
# 查看服务状态
systemctl status railway-exam

# 查看实时日志
journalctl -u railway-exam -f

# 重启服务
systemctl restart railway-exam

# 更新代码（拉取最新版本）
cd /root/project && git pull && systemctl restart railway-exam
```

---

## 性能优化（1000人并发）

部署完成后可选：

```bash
# 1. 开启 GZip 压缩（已内置）
# 2. 增加 uvicorn workers
sed -i 's/--workers 4/--workers 8/' /etc/systemd/system/railway-exam.service
systemctl daemon-reload && systemctl restart railway-exam

# 3. 挂 CDN（腾讯云 CDN 首月免费）
# 在腾讯云控制台 → CDN → 添加加速域名 → 源站填写 http://IP:8080
```

---

**有问题随时问我，帮你远程排查！**