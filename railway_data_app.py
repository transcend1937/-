"""铁路招录数据查询 - 完全自包含，不依赖 src/ 目录"""
import os
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

WORKSPACE = os.path.dirname(os.path.abspath(__file__))

# 加载数据
DATA_PATH = os.path.join(WORKSPACE, "assets", "railway_data.json")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    RAILWAY_DATA = json.load(f)

app = FastAPI()

SPA_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2025铁路局招录数据查询</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif;
    background: #f0f2f5;
    color: #1f2937;
    min-height: 100vh;
}
.header {
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    color: white;
    padding: 20px 16px 16px;
    text-align: center;
}
.header h1 { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
.header .sub { font-size: 13px; color: rgba(255,255,255,0.7); }
.notice {
    background: #fef3c7;
    color: #92400e;
    text-align: center;
    padding: 10px 16px;
    font-size: 13px;
    border-bottom: 1px solid #fde68a;
}
.tabs {
    display: flex;
    background: white;
    border-bottom: 1px solid #e5e7eb;
    position: sticky;
    top: 0;
    z-index: 10;
}
.tab {
    flex: 1;
    text-align: center;
    padding: 14px 8px;
    font-size: 15px;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
}
.tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.tab .badge {
    display: inline-block;
    background: #e5e7eb;
    color: #6b7280;
    font-size: 11px;
    padding: 1px 8px;
    border-radius: 10px;
    margin-left: 4px;
}
.tab.active .badge { background: #dbeafe; color: #2563eb; }
.search-bar {
    padding: 12px 16px;
    background: white;
}
.search-bar input {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}
.search-bar input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.content {
    max-width: 800px;
    margin: 0 auto;
    padding: 12px 12px 80px;
}
.stats-row {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}
.stat-card {
    flex: 1;
    background: white;
    border-radius: 12px;
    padding: 14px 12px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.stat-card .num { font-size: 24px; font-weight: 700; color: #2563eb; }
.stat-card .label { font-size: 12px; color: #6b7280; margin-top: 2px; }
.bureau-grid { display: flex; flex-direction: column; gap: 8px; }
.bureau-card {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: all 0.2s;
    cursor: pointer;
}
.bureau-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.bureau-card .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
}
.bureau-card .card-header .name { font-size: 16px; font-weight: 600; }
.bureau-card .card-header .total { font-size: 18px; font-weight: 700; color: #2563eb; }
.bureau-card .card-header .total small { font-size: 12px; font-weight: 400; color: #6b7280; }
.bureau-card .card-header .arrow { color: #9ca3af; font-size: 18px; margin-left: 8px; }
.bureau-card .card-detail { display: none; border-top: 1px solid #f3f4f6; padding: 8px 16px 12px; }
.bureau-card.expanded .card-detail { display: block; }
.bureau-card .major-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    font-size: 14px;
    border-bottom: 1px solid #f9fafb;
}
.bureau-card .major-row:last-child { border-bottom: none; }
.bureau-card .major-row .mname { color: #374151; }
.bureau-card .major-row .mcount { font-weight: 600; color: #2563eb; }
.bureau-card .major-row .mbreakdown { color: #9ca3af; font-size: 12px; }
.backdrop {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 20;
    justify-content: center;
    align-items: flex-start;
    padding-top: 40px;
}
.modal {
    background: white;
    border-radius: 20px;
    width: 90%;
    max-width: 480px;
    max-height: 80vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.modal-header {
    padding: 16px 20px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.modal-header h2 { font-size: 18px; font-weight: 600; }
.modal-header .close { width: 32px; height: 32px; border-radius: 50%; border: none; background: #f3f4f6; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.modal-body { padding: 12px 20px 20px; overflow-y: auto; flex: 1; }
.modal-body .info-line { display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px; border-bottom: 1px solid #f3f4f6; }
.modal-body .info-line:last-child { border-bottom: none; }
.modal-body .info-line .ilabel { color: #6b7280; }
.modal-body .info-line .ivalue { font-weight: 600; }
.bureau-chip { display: inline-block; background: #eff6ff; color: #2563eb; font-size: 12px; padding: 2px 10px; border-radius: 12px; margin: 2px 3px; }
.summary {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: white;
    border-top: 1px solid #e5e7eb;
    padding: 10px 16px;
    text-align: center;
    font-size: 12px;
    color: #9ca3af;
    z-index: 5;
}
</style>
</head>
<body>
<div class="header">
    <h1>🚂 2025级 铁路局招录数据</h1>
    <div class="sub">湖南铁道职业技术学院（东校区）</div>
</div>
<div class="notice">📢 温馨提示：所有招录数据均来自中国铁路人才招聘网的官方公示</div>
<div class="tabs">
    <div class="tab active" onclick="switchTab('bureau')">🏢 按路局 <span class="badge" id="bureauCount">0</span></div>
    <div class="tab" onclick="switchTab('major')">📚 按专业 <span class="badge" id="majorCount">0</span></div>
</div>
<div class="search-bar"><input type="text" id="searchInput" placeholder="🔍 搜索路局或专业名称..." oninput="filterData()"></div>
<div class="content" id="contentArea">
    <div class="stats-row" id="statsRow"></div>
    <div class="bureau-grid" id="dataList"></div>
</div>
<div class="summary" id="summaryBar">数据加载中...</div>
<div class="backdrop" id="modalBackdrop" onclick="closeModal()">
    <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-header"><h2 id="modalTitle">详情</h2><button class="close" onclick="closeModal()">✕</button></div>
        <div class="modal-body" id="modalBody"></div>
    </div>
</div>
<script>
let data = null, currentTab='bureau';
async function init(){
    try{
        const r=await fetch('/railway/api/data');
        data=await r.json();
        document.getElementById('bureauCount').textContent=data.total_bureaus;
        document.getElementById('majorCount').textContent=data.total_majors;
        document.getElementById('summaryBar').textContent='📊 共 '+data.total_bureaus+' 个路局 · '+data.total_majors+' 个专业 · '+data.grand_total+' 人招录数据';
        renderBureau();
    }catch(e){
        document.getElementById('summaryBar').textContent='⚠️ 数据加载失败，请刷新重试';
    }
}
function switchTab(t){
    currentTab=t;
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.tab')[t==='bureau'?0:1].classList.add('active');
    document.getElementById('searchInput').value='';
    filterData();
}
function filterData(){
    const q=document.getElementById('searchInput').value.trim().toLowerCase();
    if(currentTab==='bureau') renderBureau(q);
    else renderMajor(q);
}
function renderBureau(query){
    let bureaus=data.bureaus;
    if(query)bureaus=bureaus.filter(b=>b.name.includes(query)||b.majors.some(m=>m.name.includes(query)));
    const total=bureaus.reduce((s,b)=>s+b.total.total,0);
    const top=bureaus.length?bureaus[0].name+' '+bureaus[0].total.total+'人':'-';
    document.getElementById('statsRow').innerHTML=
        '<div class="stat-card"><div class="num">'+bureaus.length+'</div><div class="label">路局</div></div>'+
        '<div class="stat-card"><div class="num">'+total+'</div><div class="label">招录人数</div></div>'+
        '<div class="stat-card"><div class="num" style="font-size:13px;line-height:1.3">'+top+'</div><div class="label">最多</div></div>';
    let html='<div class="bureau-grid">';
    bureaus.forEach((b,i)=>{
        html+='<div class="bureau-card" onclick="this.classList.toggle(\'expanded\')">'+
            '<div class="card-header"><span class="name">🚉 '+b.name+'</span>'+
            '<span><span class="total">'+b.total.total+'<small>人</small></span><span class="arrow">▾</span></span></div>'+
            '<div class="card-detail"><div style="display:flex;gap:8px;margin-bottom:6px;font-size:12px;color:#6b7280">'+
            '<span>👨 男'+b.total.male+' ('+b.total.male_pct+')</span>'+
            '<span>👩 女'+b.total.female+' ('+b.total.female_pct+')</span>'+
            '<span>📚 '+b.majors.length+'个专业</span></div>';
        b.majors.forEach(m=>{
            html+='<div class="major-row"><span class="mname">'+m.name+'</span>'+
                '<span><span class="mcount">'+m.total+'</span> <span class="mbreakdown">男'+m.male+' 女'+m.female+'</span></span></div>';
        });
        html+='</div></div>';
    });
    html+='</div>';
    document.getElementById('dataList').innerHTML=html;
}
function renderMajor(query){
    let majors=data.majors;
    if(query)majors=majors.filter(m=>m.name.includes(query));
    const totalMale=majors.reduce((s,m)=>s+m.male,0);
    const totalFemale=majors.reduce((s,m)=>s+m.female,0);
    const totalAll=majors.reduce((s,m)=>s+m.total,0);
    const top=majors.length?majors[0].name+' '+majors[0].total+'人':'-';
    document.getElementById('statsRow').innerHTML=
        '<div class="stat-card"><div class="num">'+majors.length+'</div><div class="label">专业</div></div>'+
        '<div class="stat-card"><div class="num">'+totalAll+'</div><div class="label">招录人数</div></div>'+
        '<div class="stat-card"><div class="num" style="font-size:13px;line-height:1.3">'+top+'</div><div class="label">最多</div></div>';
    let html='<div class="bureau-grid">';
    majors.forEach((m,i)=>{
        html+='<div class="bureau-card" onclick="showMajorDetail('+i+')">'+
            '<div class="card-header"><span class="name">📖 '+m.name+'</span>'+
            '<span><span class="total">'+m.total+'<small>人</small></span><span class="arrow">▸</span></span></div>'+
            '<div class="card-detail"><div style="display:flex;gap:8px;margin-bottom:6px;font-size:12px;color:#6b7280">'+
            '<span>👨 男'+m.male+'</span><span>👩 女'+m.female+'</span>'+
            '<span>🏢 '+m.bureau_count+'个路局</span></div></div></div>';
    });
    html+='</div>';
    document.getElementById('dataList').innerHTML=html;
}
function showMajorDetail(idx){
    const m=data.majors[idx];
    document.getElementById('modalTitle').textContent='📖 '+m.name;
    let html='<div class="info-line"><span class="ilabel">招录总人数</span><span class="ivalue" style="color:#2563eb;font-size:18px">'+m.total+'</span></div>'+
        '<div class="info-line"><span class="ilabel">男生</span><span class="ivalue">'+m.male+' ('+m.male_pct+')</span></div>'+
        '<div class="info-line"><span class="ilabel">女生</span><span class="ivalue">'+m.female+' ('+m.female_pct+')</span></div>'+
        '<div class="info-line"><span class="ilabel">覆盖路局</span><span class="ivalue">'+m.bureau_count+'个</span></div>'+
        '<div style="margin-top:10px"><div style="font-size:13px;color:#6b7280;margin-bottom:6px">招录路局：</div>';
    m.bureaus.forEach(b=>{html+='<span class="bureau-chip">'+b+'</span>';});
    html+='</div>';
    document.getElementById('modalBody').innerHTML=html;
    document.getElementById('modalBackdrop').style.display='flex';
}
function closeModal(){document.getElementById('modalBackdrop').style.display='none';}
init();
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return SPA_HTML

@app.get("/api/data")
async def get_data():
    return RAILWAY_DATA