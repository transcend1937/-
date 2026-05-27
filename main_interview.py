"""铁路院校模拟面试 - 启动入口"""
import sys
import os

# 将 src 目录加入 PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    uvicorn.run("interview.app:app", host="0.0.0.0", port=port, workers=1)