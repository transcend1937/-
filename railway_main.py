"""Railway 独立入口 - 无需 Coze 依赖"""
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="铁路校招服务平台")

# 挂载静态文件
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 机考题库
from src.exam.app import app as exam_app
app.mount("/exam", exam_app)

# 招录数据查询
from src.railway.app import app as railway_app
app.mount("/railway", railway_app)

# 首页导航
@app.get("/", response_class=HTMLResponse)
async def home():
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>铁路校招服务平台</title>
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
.card .tag{
    display:inline-block;font-size:11px;padding:3px 10px;border-radius:100px;margin-top:8px
}
.tag.exam{background:rgba(59,130,246,0.15);color:#60a5fa}
.tag.interview{background:rgba(139,92,246,0.15);color:#a78bfa}
.tag.data{background:rgba(34,197,94,0.15);color:#34d399}
.footer{text-align:center;font-size:12px;color:#475569;margin-top:40px}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🚂 铁路校招服务平台</h1>
        <p>题库练习 · 面试模拟 · 招录数据查询</p>
    </div>
    <a class="card" href="/exam/">
        <div class="icon">📝</div>
        <h2>广铁机考模拟题库</h2>
        <p>铁路岗位招聘笔试练习，185道真题在线刷</p>
        <span class="tag exam">📖 题库练习</span>
    </a>
    <a class="card" href="/railway/">
        <div class="icon">📊</div>
        <h2>铁路局招录数据查询</h2>
        <p>18家铁路局2025届招录数据，按路局或专业分类查询</p>
        <span class="tag data">📋 数据查询</span>
    </a>
    <a class="card" href="https://7744570e-7af9-4d80-9dcb-db4a950df08e.dev.coze.site/interview/">
        <div class="icon">🎙</div>
        <h2>铁路校招模拟面试</h2>
        <p>AI面试官全程语音提问，回答即评，改进建议</p>
        <span class="tag interview">🎤 语音面试</span>
    </a>
    <div class="footer">所有数据均来自中国铁路人才招聘网官方公示</div>
</div>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)