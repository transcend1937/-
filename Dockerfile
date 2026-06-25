# 腾讯云部署 —— 广铁机考服务平台
# 基于 Python 3.12，使用 uvicorn 运行

FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 指定端口
ENV PORT=8080

# 启动
CMD ["sh", "-c", "uvicorn railway_main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 4"]