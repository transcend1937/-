"""铁路服务平台 - 题库 + 招录查询"""
import os
import sys
import json
import importlib.util
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from src.utils.analytics import record_from_request, get_stats

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(WORKSPACE, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# ========== 加载子应用 ==========
# 题库
spec = importlib.util.spec_from_file_location("exam_app", os.path.join(WORKSPACE, "src", "exam", "app.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
exam_app = mod.app

# 招录数据查询
from railway_data_app import app as railway_app

# ========== 主应用 ==========
app = FastAPI(title="广铁机考题库")
app.add_middleware(GZipMiddleware, minimum_size=500)

# 首页
HOME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>广铁机考服务平台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    background:linear-gradient(135deg,#0a1628,#1a2a4a,#0d1b3e);
    min-height:100vh;color:#e2e8f0;display:flex;flex-direction:column;align-items:center;
    padding:40px 20px
}
.container{max-width:600px;width:100%}
.header{text-align:center;margin-bottom:40px}
.header h1{font-size:28px;background:linear-gradient(90deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.header p{font-size:14px;color:#64748b}
.card{
    display:block;text-decoration:none;
    background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
    border-radius:16px;padding:24px;margin-bottom:16px;
    transition:all 0.3s;cursor:pointer
}
.card:hover{background:rgba(255,255,255,0.08);border-color:rgba(96,165,250,0.3);transform:translateY(-2px)}
.card .icon{font-size:36px;margin-bottom:8px}
.card h2{font-size:18px;color:#e2e8f0;margin-bottom:4px}
.card p{font-size:13px;color:#64748b;line-height:1.5}
.card .tag{display:inline-block;font-size:11px;padding:3px 10px;border-radius:100px;margin-top:8px}
.tag.exam{background:rgba(59,130,246,0.15);color:#60a5fa}
.tag.data{background:rgba(34,197,94,0.15);color:#34d399}
.footer{text-align:center;font-size:12px;color:#475569;margin-top:40px}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🚂 广铁机考服务平台</h1>
        <p>题库练习 · 招录数据查询</p>
    </div>
    <a class="card" href="/exam/">
        <div class="icon">📝</div>
        <h2>广铁机考模拟题库</h2>
        <p>铁路岗位招聘笔试练习，193道真题在线刷</p>
        <span class="tag exam">📖 题库练习</span>
    </a>
    <a class="card" href="/railway/">
        <div class="icon">📊</div>
        <h2>铁路局招录数据查询</h2>
        <p>18家铁路局2025届招录数据，按路局或专业分类查询</p>
        <span class="tag data">📋 数据查询</span>
    </a>
    <div class="footer">所有数据均来自中国铁路人才招聘网官方公示</div>
</div>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HOME_HTML

# ========== 访客统计（轻量，保留）==========
@app.post("/api/track")
async def track(request: Request):
    body = await request.json()
    record_from_request(
        page=body.get("p", "/"),
        request_headers=dict(request.headers),
        title=body.get("t", ""),
    )
    return {"ok": True}

@app.get("/api/analytics")
async def analytics(days: int = 7):
    return get_stats(days=days)

# ========== 挂载子应用 ==========
app.mount("/exam", exam_app)
app.mount("/railway", railway_app)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)