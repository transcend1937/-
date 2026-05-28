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
/* 专业详情 - 各路局表格 */
.bureau-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
.bureau-table th { background: #f8fafc; padding: 8px 6px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb; }
.bureau-table td { padding: 7px 6px; border-bottom: 1px solid #f3f4f6; }
.bureau-table tr:hover td { background: #fafafa; }
.bureau-table .num { text-align: center; font-variant-numeric: tabular-nums; }
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
const EMBEDDED_DATA = {"total_bureaus": 18, "total_majors": 23, "grand_total": 1000, "bureaus": [{"name": "广州局", "total": {"male": 385, "female": 73, "total": 458}, "majors": [{"name": "铁道交通运营管理", "male": 73, "female": 22, "total": 95, "male_pct": "76.8%", "female_pct": "23.2%"}, {"name": "铁道机车运用与维护", "male": 52, "female": 0, "total": 52, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道车辆技术", "male": 45, "female": 6, "total": 51, "male_pct": "88.2%", "female_pct": "11.8%"}, {"name": "动车组检修技术", "male": 35, "female": 1, "total": 36, "male_pct": "97.2%", "female_pct": "2.8%"}, {"name": "铁道工程技术", "male": 36, "female": 0, "total": 36, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道交通运营管理", "male": 9, "female": 20, "total": 29, "male_pct": "31.0%", "female_pct": "69.0%"}, {"name": "铁道信号自动控制", "male": 18, "female": 6, "total": 24, "male_pct": "75.0%", "female_pct": "25.0%"}, {"name": "高速铁路综合维修技术", "male": 18, "female": 2, "total": 20, "male_pct": "90.0%", "female_pct": "10.0%"}, {"name": "城市轨道交通机电技术", "male": 18, "female": 0, "total": 18, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道车辆应用技术", "male": 13, "female": 3, "total": 16, "male_pct": "81.2%", "female_pct": "18.8%"}, {"name": "城市轨道交通通信信号技术", "male": 14, "female": 2, "total": 16, "male_pct": "87.5%", "female_pct": "12.5%"}, {"name": "高速铁路施工与维护", "male": 11, "female": 2, "total": 13, "male_pct": "84.6%", "female_pct": "15.4%"}, {"name": "铁道通信与信息化技术", "male": 7, "female": 3, "total": 10, "male_pct": "70.0%", "female_pct": "30.0%"}, {"name": "电气自动化技术", "male": 8, "female": 1, "total": 9, "male_pct": "88.9%", "female_pct": "11.1%"}, {"name": "铁道供电技术", "male": 8, "female": 1, "total": 9, "male_pct": "88.9%", "female_pct": "11.1%"}, {"name": "城市轨道交通供配电技术", "male": 4, "female": 3, "total": 7, "male_pct": "57.1%", "female_pct": "42.9%"}, {"name": "机电一体化技术", "male": 7, "female": 0, "total": 7, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "机械设计与制造", "male": 5, "female": 0, "total": 5, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "数控技术", "male": 2, "female": 1, "total": 3, "male_pct": "66.7%", "female_pct": "33.3%"}, {"name": "现代物流管理", "male": 2, "female": 0, "total": 2, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "南昌局", "total": {"male": 126, "female": 57, "total": 183}, "majors": [{"name": "铁道机车运用与维护", "male": 27, "female": 5, "total": 32, "male_pct": "84.4%", "female_pct": "15.6%"}, {"name": "铁道交通运营管理", "male": 17, "female": 13, "total": 30, "male_pct": "56.7%", "female_pct": "43.3%"}, {"name": "动车组检修技术", "male": 21, "female": 7, "total": 28, "male_pct": "75.0%", "female_pct": "25.0%"}, {"name": "现代物流管理", "male": 12, "female": 6, "total": 18, "male_pct": "66.7%", "female_pct": "33.3%"}, {"name": "铁道车辆技术", "male": 5, "female": 7, "total": 12, "male_pct": "41.7%", "female_pct": "58.3%"}, {"name": "城市轨道交通机电技术", "male": 6, "female": 4, "total": 10, "male_pct": "60.0%", "female_pct": "40.0%"}, {"name": "高速铁路施工与维护", "male": 6, "female": 2, "total": 8, "male_pct": "75.0%", "female_pct": "25.0%"}, {"name": "城市轨道交通运营管理", "male": 5, "female": 2, "total": 7, "male_pct": "71.4%", "female_pct": "28.6%"}, {"name": "城市轨道车辆应用技术", "male": 7, "female": 0, "total": 7, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道供电技术", "male": 3, "female": 3, "total": 6, "male_pct": "50.0%", "female_pct": "50.0%"}, {"name": "铁道信号自动控制", "male": 2, "female": 3, "total": 5, "male_pct": "40.0%", "female_pct": "60.0%"}, {"name": "铁道工程技术", "male": 4, "female": 1, "total": 5, "male_pct": "80.0%", "female_pct": "20.0%"}, {"name": "铁道通信与信息化技术", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "机械设计与制造", "male": 1, "female": 2, "total": 3, "male_pct": "33.3%", "female_pct": "66.7%"}, {"name": "高速铁路综合维修技术", "male": 2, "female": 1, "total": 3, "male_pct": "66.7%", "female_pct": "33.3%"}, {"name": "智能控制技术", "male": 2, "female": 0, "total": 2, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道交通通信信号技术", "male": 0, "female": 1, "total": 1, "male_pct": "0.0%", "female_pct": "100.0%"}, {"name": "电气自动化技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "机电一体化技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "机电设备技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "上海局", "total": {"male": 84, "female": 3, "total": 87}, "majors": [{"name": "铁道工程技术", "male": 17, "female": 0, "total": 17, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "动车组检修技术", "male": 16, "female": 0, "total": 16, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道机车运用与维护", "male": 10, "female": 0, "total": 10, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道车辆应用技术", "male": 9, "female": 0, "total": 9, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道信号自动控制", "male": 5, "female": 1, "total": 6, "male_pct": "83.3%", "female_pct": "16.7%"}, {"name": "铁道供电技术", "male": 6, "female": 0, "total": 6, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "高速铁路施工与维护", "male": 5, "female": 0, "total": 5, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道交通运营管理", "male": 4, "female": 0, "total": 4, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道车辆技术", "male": 4, "female": 0, "total": 4, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "电气自动化技术", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道交通供配电技术", "male": 2, "female": 0, "total": 2, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道交通通信信号技术", "male": 0, "female": 2, "total": 2, "male_pct": "0.0%", "female_pct": "100.0%"}, {"name": "机电一体化技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道交通运营管理", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道通信与信息化技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "昆明局", "total": {"male": 40, "female": 3, "total": 43}, "majors": [{"name": "铁道交通运营管理", "male": 9, "female": 1, "total": 10, "male_pct": "90.0%", "female_pct": "10.0%"}, {"name": "铁道供电技术", "male": 7, "female": 1, "total": 8, "male_pct": "87.5%", "female_pct": "12.5%"}, {"name": "铁道机车运用与维护", "male": 6, "female": 0, "total": 6, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "动车组检修技术", "male": 5, "female": 0, "total": 5, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道交通机电技术", "male": 5, "female": 0, "total": 5, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道信号自动控制", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道车辆技术", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "电气自动化技术", "male": 1, "female": 1, "total": 2, "male_pct": "50.0%", "female_pct": "50.0%"}, {"name": "机械设计与制造", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "武汉局", "total": {"male": 29, "female": 12, "total": 41}, "majors": [{"name": "动车组检修技术", "male": 9, "female": 1, "total": 10, "male_pct": "90.0%", "female_pct": "10.0%"}, {"name": "铁道供电技术", "male": 6, "female": 2, "total": 8, "male_pct": "75.0%", "female_pct": "25.0%"}, {"name": "铁道机车运用与维护", "male": 7, "female": 1, "total": 8, "male_pct": "87.5%", "female_pct": "12.5%"}, {"name": "铁道交通运营管理", "male": 3, "female": 3, "total": 6, "male_pct": "50.0%", "female_pct": "50.0%"}, {"name": "铁道工程技术", "male": 2, "female": 2, "total": 4, "male_pct": "50.0%", "female_pct": "50.0%"}, {"name": "铁道信号自动控制", "male": 0, "female": 2, "total": 2, "male_pct": "0.0%", "female_pct": "100.0%"}, {"name": "铁道车辆技术", "male": 1, "female": 1, "total": 2, "male_pct": "50.0%", "female_pct": "50.0%"}, {"name": "城市轨道交通机电技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "兰州局", "total": {"male": 29, "female": 6, "total": 35}, "majors": [{"name": "铁道机车运用与维护", "male": 5, "female": 0, "total": 5, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道车辆技术", "male": 7, "female": 1, "total": 8, "male_pct": "87.5%", "female_pct": "12.5%"}, {"name": "铁道供电技术", "male": 4, "female": 0, "total": 4, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道交通运营管理", "male": 5, "female": 5, "total": 10, "male_pct": "50%", "female_pct": "50%"}, {"name": "铁道工程技术", "male": 5, "female": 0, "total": 5, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道信号控制", "male": 3, "female": 0, "total": 3, "male_pct": "100%", "female_pct": "0%"}]}, {"name": "青藏集团", "total": {"male": 21, "female": 9, "total": 30}, "majors": [{"name": "铁道机车运用与维护", "male": 7, "female": 0, "total": 7, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "动车组检修技术", "male": 4, "female": 1, "total": 5, "male_pct": "80.0%", "female_pct": "20.0%"}, {"name": "铁道车辆技术", "male": 4, "female": 3, "total": 7, "male_pct": "57.14.0%", "female_pct": "42.86%"}, {"name": "铁道供电技术", "male": 3, "female": 1, "total": 4, "male_pct": "75.0%", "female_pct": "25.0%"}, {"name": "铁道交通运营管理", "male": 0, "female": 3, "total": 3, "male_pct": "0%", "female_pct": "100%"}, {"name": "铁道工程技术", "male": 2, "female": 0, "total": 2, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道信号控制", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道通信与信息化技术", "male": 0, "female": 1, "total": 1, "male_pct": "0%", "female_pct": "100%"}]}, {"name": "乌鲁木齐局", "total": {"male": 0, "female": 0, "total": 25}, "majors": [{"name": "铁道机车运用与维护", "male": 0, "female": 0, "total": 2, "male_pct": "-", "female_pct": "-"}, {"name": "铁道车辆技术", "male": 0, "female": 0, "total": 7, "male_pct": "-", "female_pct": "-"}, {"name": "城市轨道车辆应用技术", "male": 0, "female": 0, "total": 6, "male_pct": "-", "female_pct": "-"}, {"name": "铁道交通运营管理", "male": 0, "female": 0, "total": 3, "male_pct": "-", "female_pct": "-"}, {"name": "城市轨道交通通信信号技术", "male": 0, "female": 0, "total": 2, "male_pct": "-", "female_pct": "-"}, {"name": "动车组检修技术", "male": 0, "female": 0, "total": 2, "male_pct": "-", "female_pct": "-"}, {"name": "铁道供电技术", "male": 0, "female": 0, "total": 1, "male_pct": "-", "female_pct": "-"}, {"name": "智能控制技术", "male": 0, "female": 0, "total": 1, "male_pct": "-", "female_pct": "-"}, {"name": "城市轨道交通运营管理", "male": 0, "female": 0, "total": 1, "male_pct": "-", "female_pct": "-"}]}, {"name": "南宁局", "total": {"male": 25, "female": 0, "total": 23}, "majors": [{"name": "铁道机车运用与维护", "male": 7, "female": 0, "total": 7, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "动车组检修技术", "male": 4, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道车辆技术", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "高速铁路施工与维护", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道供电技术", "male": 2, "female": 0, "total": 2, "male_pct": "100%", "female_pct": "0%"}, {"name": "城市轨道交通机电技术", "male": 2, "female": 0, "total": 2, "male_pct": "100%", "female_pct": "0%"}, {"name": "城市轨道车辆应用技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道工程技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "智能控制技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "城市轨道交通运营管理", "male": 1, "female": 0, "total": 0, "male_pct": "100%", "female_pct": "0%"}]}, {"name": "太原局", "total": {"male": 15, "female": 1, "total": 16}, "majors": [{"name": "铁道机车运用与维护", "male": 6, "female": 1, "total": 7, "male_pct": "85.71", "female_pct": "14.29%"}, {"name": "铁道车辆技术", "male": 4, "female": 0, "total": 4, "male_pct": "100%", "female_pct": "0%"}, {"name": "智能控制技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道交通运营管理", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道工程技术", "male": 3, "female": 0, "total": 3, "male_pct": "100%", "female_pct": "0%"}]}, {"name": "济南局", "total": {"male": 14, "female": 1, "total": 15}, "majors": [{"name": "铁道车辆技术", "male": 6, "female": 0, "total": 6, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "动车组检修技术", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道机车运用与维护", "male": 2, "female": 0, "total": 2, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道工程技术", "male": 1, "female": 1, "total": 2, "male_pct": "50.0%", "female_pct": "50.0%"}, {"name": "城市轨道交通运营管理", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道信号自动控制", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "北京局", "total": {"male": 16, "female": 0, "total": 14}, "majors": [{"name": "铁道机车运用与维护", "male": 4, "female": 0, "total": 4, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "动车组检修技术", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道车辆技术", "male": 2, "female": 0, "total": 0, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "智能控制技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道交通运营管理", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道工程技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "数控技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "电气自动化技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "城市轨道交通运营管理", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}, {"name": "城市轨道交通供配电技术", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}]}, {"name": "成都局", "total": {"male": 16, "female": 6, "total": 13}, "majors": [{"name": "铁道交通运营管理", "male": 2, "female": 0, "total": 0, "male_pct": "100.0%", "female_pct": "0%"}, {"name": "铁道供电技术", "male": 2, "female": 0, "total": 2, "male_pct": "100%", "female_pct": "0%"}, {"name": "铁道机车运用与维护", "male": 5, "female": 0, "total": 5, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "动车组检修技术", "male": 1, "female": 0, "total": 0, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道车辆应用技术", "male": 3, "female": 0, "total": 0, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道信号控制", "male": 0, "female": 1, "total": 0, "male_pct": "0%", "female_pct": "100%"}, {"name": "铁道车辆技术", "male": 0, "female": 2, "total": 0, "male_pct": "0%", "female_pct": "100%"}, {"name": "机电设备技术", "male": 0, "female": 1, "total": 1, "male_pct": "100%", "female_pct": "100%"}, {"name": "智能控制技术", "male": 0, "female": 1, "total": 1, "male_pct": "0%", "female_pct": "100%"}, {"name": "高速铁路综合维修技术", "male": 2, "female": 0, "total": 2, "male_pct": "100%", "female_pct": "0%"}, {"name": "城市轨道交通供配电技术", "male": 0, "female": 1, "total": 1, "male_pct": "0%", "female_pct": "100%"}, {"name": "高速铁路施工与维护", "male": 1, "female": 0, "total": 1, "male_pct": "100%", "female_pct": "0%"}]}, {"name": "沈阳局", "total": {"male": 7, "female": 0, "total": 7}, "majors": [{"name": "铁道车辆技术", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道机车运用与维护", "male": 3, "female": 0, "total": 3, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道工程技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "西安局", "total": {"male": 5, "female": 0, "total": 5}, "majors": [{"name": "铁道机车运用与维护", "male": 2, "female": 0, "total": 2, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "城市轨道车辆应用技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "电气自动化技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道供电技术", "male": 1, "female": 0, "total": 1, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "呼和浩特局", "total": {"male": 4, "female": 0, "total": 4}, "majors": [{"name": "铁道车辆技术", "male": 2, "female": 0, "total": 2, "male_pct": "100.0%", "female_pct": "0.0%"}, {"name": "铁道机车运用与维护", "male": 2, "female": 0, "total": 2, "male_pct": "100.0%", "female_pct": "0.0%"}]}, {"name": "哈尔滨局", "total": {"male": 0, "female": 1, "total": 1}, "majors": [{"name": "铁道交通运营管理", "male": 0, "female": 1, "total": 1, "male_pct": "0%", "female_pct": "100%"}]}, {"name": "郑州局", "total": {"male": 0, "female": 0, "total": 0}, "majors": []}], "majors": [{"name": "铁道交通运营管理", "male": 112, "female": 48, "total": 160, "male_pct": "70.0%", "female_pct": "30.0%", "bureau_count": 11, "bureaus": ["广州局", "南昌局", "昆明局", "兰州局", "武汉局", "青藏集团", "乌鲁木齐局", "上海局", "太原局", "北京局", "哈尔滨局"], "bureau_details": [{"name": "广州局", "male": 73, "female": 22, "total": 95}, {"name": "南昌局", "male": 17, "female": 13, "total": 30}, {"name": "昆明局", "male": 9, "female": 1, "total": 10}, {"name": "兰州局", "male": 5, "female": 5, "total": 10}, {"name": "武汉局", "male": 3, "female": 3, "total": 6}, {"name": "青藏集团", "male": 0, "female": 3, "total": 3}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 3}, {"name": "上海局", "male": 1, "female": 0, "total": 1}, {"name": "太原局", "male": 1, "female": 0, "total": 1}, {"name": "北京局", "male": 1, "female": 0, "total": 1}, {"name": "哈尔滨局", "male": 0, "female": 1, "total": 1}]}, {"name": "铁道机车运用与维护", "male": 145, "female": 7, "total": 152, "male_pct": "95.4%", "female_pct": "4.6%", "bureau_count": 16, "bureaus": ["广州局", "南昌局", "上海局", "武汉局", "青藏集团", "南宁局", "太原局", "昆明局", "兰州局", "成都局", "北京局", "沈阳局", "乌鲁木齐局", "济南局", "西安局", "呼和浩特局"], "bureau_details": [{"name": "广州局", "male": 52, "female": 0, "total": 52}, {"name": "南昌局", "male": 27, "female": 5, "total": 32}, {"name": "上海局", "male": 10, "female": 0, "total": 10}, {"name": "武汉局", "male": 7, "female": 1, "total": 8}, {"name": "青藏集团", "male": 7, "female": 0, "total": 7}, {"name": "南宁局", "male": 7, "female": 0, "total": 7}, {"name": "太原局", "male": 6, "female": 1, "total": 7}, {"name": "昆明局", "male": 6, "female": 0, "total": 6}, {"name": "兰州局", "male": 5, "female": 0, "total": 5}, {"name": "成都局", "male": 5, "female": 0, "total": 5}, {"name": "北京局", "male": 4, "female": 0, "total": 4}, {"name": "沈阳局", "male": 3, "female": 0, "total": 3}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 2}, {"name": "济南局", "male": 2, "female": 0, "total": 2}, {"name": "西安局", "male": 2, "female": 0, "total": 2}, {"name": "呼和浩特局", "male": 2, "female": 0, "total": 2}]}, {"name": "动车组检修技术", "male": 101, "female": 10, "total": 111, "male_pct": "91.0%", "female_pct": "9.0%", "bureau_count": 10, "bureaus": ["广州局", "南昌局", "上海局", "武汉局", "昆明局", "青藏集团", "南宁局", "济南局", "北京局", "乌鲁木齐局"], "bureau_details": [{"name": "广州局", "male": 35, "female": 1, "total": 36}, {"name": "南昌局", "male": 21, "female": 7, "total": 28}, {"name": "上海局", "male": 16, "female": 0, "total": 16}, {"name": "武汉局", "male": 9, "female": 1, "total": 10}, {"name": "昆明局", "male": 5, "female": 0, "total": 5}, {"name": "青藏集团", "male": 4, "female": 1, "total": 5}, {"name": "南宁局", "male": 4, "female": 0, "total": 3}, {"name": "济南局", "male": 3, "female": 0, "total": 3}, {"name": "北京局", "male": 3, "female": 0, "total": 3}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 2}]}, {"name": "铁道车辆技术", "male": 89, "female": 20, "total": 109, "male_pct": "81.7%", "female_pct": "18.3%", "bureau_count": 13, "bureaus": ["广州局", "南昌局", "兰州局", "青藏集团", "乌鲁木齐局", "济南局", "上海局", "太原局", "昆明局", "南宁局", "沈阳局", "武汉局", "呼和浩特局"], "bureau_details": [{"name": "广州局", "male": 45, "female": 6, "total": 51}, {"name": "南昌局", "male": 5, "female": 7, "total": 12}, {"name": "兰州局", "male": 7, "female": 1, "total": 8}, {"name": "青藏集团", "male": 4, "female": 3, "total": 7}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 7}, {"name": "济南局", "male": 6, "female": 0, "total": 6}, {"name": "上海局", "male": 4, "female": 0, "total": 4}, {"name": "太原局", "male": 4, "female": 0, "total": 4}, {"name": "昆明局", "male": 3, "female": 0, "total": 3}, {"name": "南宁局", "male": 3, "female": 0, "total": 3}, {"name": "沈阳局", "male": 3, "female": 0, "total": 3}, {"name": "武汉局", "male": 1, "female": 1, "total": 2}, {"name": "呼和浩特局", "male": 2, "female": 0, "total": 2}]}, {"name": "铁道工程技术", "male": 73, "female": 4, "total": 77, "male_pct": "94.8%", "female_pct": "5.2%", "bureau_count": 11, "bureaus": ["广州局", "上海局", "南昌局", "兰州局", "武汉局", "太原局", "青藏集团", "济南局", "南宁局", "北京局", "沈阳局"], "bureau_details": [{"name": "广州局", "male": 36, "female": 0, "total": 36}, {"name": "上海局", "male": 17, "female": 0, "total": 17}, {"name": "南昌局", "male": 4, "female": 1, "total": 5}, {"name": "兰州局", "male": 5, "female": 0, "total": 5}, {"name": "武汉局", "male": 2, "female": 2, "total": 4}, {"name": "太原局", "male": 3, "female": 0, "total": 3}, {"name": "青藏集团", "male": 2, "female": 0, "total": 2}, {"name": "济南局", "male": 1, "female": 1, "total": 2}, {"name": "南宁局", "male": 1, "female": 0, "total": 1}, {"name": "北京局", "male": 1, "female": 0, "total": 1}, {"name": "沈阳局", "male": 1, "female": 0, "total": 1}]}, {"name": "铁道供电技术", "male": 42, "female": 8, "total": 50, "male_pct": "84.0%", "female_pct": "16.0%", "bureau_count": 11, "bureaus": ["广州局", "昆明局", "武汉局", "南昌局", "上海局", "兰州局", "青藏集团", "南宁局", "成都局", "乌鲁木齐局", "西安局"], "bureau_details": [{"name": "广州局", "male": 8, "female": 1, "total": 9}, {"name": "昆明局", "male": 7, "female": 1, "total": 8}, {"name": "武汉局", "male": 6, "female": 2, "total": 8}, {"name": "南昌局", "male": 3, "female": 3, "total": 6}, {"name": "上海局", "male": 6, "female": 0, "total": 6}, {"name": "兰州局", "male": 4, "female": 0, "total": 4}, {"name": "青藏集团", "male": 3, "female": 1, "total": 4}, {"name": "南宁局", "male": 2, "female": 0, "total": 2}, {"name": "成都局", "male": 2, "female": 0, "total": 2}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 1}, {"name": "西安局", "male": 1, "female": 0, "total": 1}]}, {"name": "城市轨道交通运营管理", "male": 21, "female": 22, "total": 43, "male_pct": "48.8%", "female_pct": "51.2%", "bureau_count": 6, "bureaus": ["广州局", "南昌局", "上海局", "乌鲁木齐局", "济南局", "北京局"], "bureau_details": [{"name": "广州局", "male": 9, "female": 20, "total": 29}, {"name": "南昌局", "male": 5, "female": 2, "total": 7}, {"name": "上海局", "male": 4, "female": 0, "total": 4}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 1}, {"name": "济南局", "male": 1, "female": 0, "total": 1}, {"name": "北京局", "male": 1, "female": 0, "total": 1}]}, {"name": "铁道信号自动控制", "male": 29, "female": 12, "total": 41, "male_pct": "70.7%", "female_pct": "29.3%", "bureau_count": 6, "bureaus": ["广州局", "上海局", "南昌局", "昆明局", "武汉局", "济南局"], "bureau_details": [{"name": "广州局", "male": 18, "female": 6, "total": 24}, {"name": "上海局", "male": 5, "female": 1, "total": 6}, {"name": "南昌局", "male": 2, "female": 3, "total": 5}, {"name": "昆明局", "male": 3, "female": 0, "total": 3}, {"name": "武汉局", "male": 0, "female": 2, "total": 2}, {"name": "济南局", "male": 1, "female": 0, "total": 1}]}, {"name": "城市轨道车辆应用技术", "male": 34, "female": 3, "total": 37, "male_pct": "91.9%", "female_pct": "8.1%", "bureau_count": 6, "bureaus": ["广州局", "上海局", "南昌局", "乌鲁木齐局", "南宁局", "西安局"], "bureau_details": [{"name": "广州局", "male": 13, "female": 3, "total": 16}, {"name": "上海局", "male": 9, "female": 0, "total": 9}, {"name": "南昌局", "male": 7, "female": 0, "total": 7}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 6}, {"name": "南宁局", "male": 1, "female": 0, "total": 1}, {"name": "西安局", "male": 1, "female": 0, "total": 1}]}, {"name": "城市轨道交通机电技术", "male": 32, "female": 4, "total": 36, "male_pct": "88.9%", "female_pct": "11.1%", "bureau_count": 5, "bureaus": ["广州局", "南昌局", "昆明局", "南宁局", "武汉局"], "bureau_details": [{"name": "广州局", "male": 18, "female": 0, "total": 18}, {"name": "南昌局", "male": 6, "female": 4, "total": 10}, {"name": "昆明局", "male": 5, "female": 0, "total": 5}, {"name": "南宁局", "male": 2, "female": 0, "total": 2}, {"name": "武汉局", "male": 1, "female": 0, "total": 1}]}, {"name": "高速铁路施工与维护", "male": 26, "female": 4, "total": 30, "male_pct": "86.7%", "female_pct": "13.3%", "bureau_count": 5, "bureaus": ["广州局", "南昌局", "上海局", "南宁局", "成都局"], "bureau_details": [{"name": "广州局", "male": 11, "female": 2, "total": 13}, {"name": "南昌局", "male": 6, "female": 2, "total": 8}, {"name": "上海局", "male": 5, "female": 0, "total": 5}, {"name": "南宁局", "male": 3, "female": 0, "total": 3}, {"name": "成都局", "male": 1, "female": 0, "total": 1}]}, {"name": "高速铁路综合维修技术", "male": 22, "female": 3, "total": 25, "male_pct": "88.0%", "female_pct": "12.0%", "bureau_count": 3, "bureaus": ["广州局", "南昌局", "成都局"], "bureau_details": [{"name": "广州局", "male": 18, "female": 2, "total": 20}, {"name": "南昌局", "male": 2, "female": 1, "total": 3}, {"name": "成都局", "male": 2, "female": 0, "total": 2}]}, {"name": "现代物流管理", "male": 14, "female": 6, "total": 20, "male_pct": "70.0%", "female_pct": "30.0%", "bureau_count": 2, "bureaus": ["南昌局", "广州局"], "bureau_details": [{"name": "南昌局", "male": 12, "female": 6, "total": 18}, {"name": "广州局", "male": 2, "female": 0, "total": 2}]}, {"name": "城市轨道交通通信信号技术", "male": 14, "female": 5, "total": 19, "male_pct": "73.7%", "female_pct": "26.3%", "bureau_count": 4, "bureaus": ["广州局", "上海局", "乌鲁木齐局", "南昌局"], "bureau_details": [{"name": "广州局", "male": 14, "female": 2, "total": 16}, {"name": "上海局", "male": 0, "female": 2, "total": 2}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 2}, {"name": "南昌局", "male": 0, "female": 1, "total": 1}]}, {"name": "电气自动化技术", "male": 15, "female": 2, "total": 17, "male_pct": "88.2%", "female_pct": "11.8%", "bureau_count": 6, "bureaus": ["广州局", "上海局", "昆明局", "南昌局", "北京局", "西安局"], "bureau_details": [{"name": "广州局", "male": 8, "female": 1, "total": 9}, {"name": "上海局", "male": 3, "female": 0, "total": 3}, {"name": "昆明局", "male": 1, "female": 1, "total": 2}, {"name": "南昌局", "male": 1, "female": 0, "total": 1}, {"name": "北京局", "male": 1, "female": 0, "total": 1}, {"name": "西安局", "male": 1, "female": 0, "total": 1}]}, {"name": "铁道通信与信息化技术", "male": 11, "female": 4, "total": 15, "male_pct": "73.3%", "female_pct": "26.7%", "bureau_count": 4, "bureaus": ["广州局", "南昌局", "上海局", "青藏集团"], "bureau_details": [{"name": "广州局", "male": 7, "female": 3, "total": 10}, {"name": "南昌局", "male": 3, "female": 0, "total": 3}, {"name": "上海局", "male": 1, "female": 0, "total": 1}, {"name": "青藏集团", "male": 0, "female": 1, "total": 1}]}, {"name": "城市轨道交通供配电技术", "male": 7, "female": 4, "total": 11, "male_pct": "63.6%", "female_pct": "36.4%", "bureau_count": 4, "bureaus": ["广州局", "上海局", "北京局", "成都局"], "bureau_details": [{"name": "广州局", "male": 4, "female": 3, "total": 7}, {"name": "上海局", "male": 2, "female": 0, "total": 2}, {"name": "北京局", "male": 1, "female": 0, "total": 1}, {"name": "成都局", "male": 0, "female": 1, "total": 1}]}, {"name": "机械设计与制造", "male": 7, "female": 2, "total": 9, "male_pct": "77.8%", "female_pct": "22.2%", "bureau_count": 3, "bureaus": ["广州局", "南昌局", "昆明局"], "bureau_details": [{"name": "广州局", "male": 5, "female": 0, "total": 5}, {"name": "南昌局", "male": 1, "female": 2, "total": 3}, {"name": "昆明局", "male": 1, "female": 0, "total": 1}]}, {"name": "机电一体化技术", "male": 9, "female": 0, "total": 9, "male_pct": "100.0%", "female_pct": "0.0%", "bureau_count": 3, "bureaus": ["广州局", "南昌局", "上海局"], "bureau_details": [{"name": "广州局", "male": 7, "female": 0, "total": 7}, {"name": "南昌局", "male": 1, "female": 0, "total": 1}, {"name": "上海局", "male": 1, "female": 0, "total": 1}]}, {"name": "智能控制技术", "male": 5, "female": 1, "total": 6, "male_pct": "83.3%", "female_pct": "16.7%", "bureau_count": 6, "bureaus": ["南昌局", "乌鲁木齐局", "南宁局", "太原局", "北京局", "成都局"], "bureau_details": [{"name": "南昌局", "male": 2, "female": 0, "total": 2}, {"name": "乌鲁木齐局", "male": 0, "female": 0, "total": 1}, {"name": "南宁局", "male": 1, "female": 0, "total": 1}, {"name": "太原局", "male": 1, "female": 0, "total": 1}, {"name": "北京局", "male": 1, "female": 0, "total": 1}, {"name": "成都局", "male": 0, "female": 1, "total": 1}]}, {"name": "铁道信号控制", "male": 4, "female": 1, "total": 5, "male_pct": "80.0%", "female_pct": "20.0%", "bureau_count": 2, "bureaus": ["兰州局", "青藏集团"], "bureau_details": [{"name": "兰州局", "male": 3, "female": 0, "total": 3}, {"name": "青藏集团", "male": 1, "female": 0, "total": 1}]}, {"name": "数控技术", "male": 3, "female": 1, "total": 4, "male_pct": "75.0%", "female_pct": "25.0%", "bureau_count": 2, "bureaus": ["广州局", "北京局"], "bureau_details": [{"name": "广州局", "male": 2, "female": 1, "total": 3}, {"name": "北京局", "male": 1, "female": 0, "total": 1}]}, {"name": "机电设备技术", "male": 1, "female": 1, "total": 2, "male_pct": "50.0%", "female_pct": "50.0%", "bureau_count": 2, "bureaus": ["南昌局", "成都局"], "bureau_details": [{"name": "南昌局", "male": 1, "female": 0, "total": 1}, {"name": "成都局", "male": 0, "female": 1, "total": 1}]}]};

let data = null, currentTab='bureau';
async function init(){
    try{
        data = EMBEDDED_DATA;
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
function toggleCard(el){el.classList.toggle('expanded');}
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
        html+='<div class="bureau-card" onclick="toggleCard(this)">'+
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
        html+='<div class="bureau-card" onclick=\'showMajorDetail("'+m.name+'")\'>'+
            '<div class="card-header"><span class="name">📖 '+m.name+'</span>'+
            '<span><span class="total">'+m.total+'<small>人</small></span><span class="arrow">▸</span></span></div>'+
            '<div class="card-detail"><div style="display:flex;gap:8px;margin-bottom:6px;font-size:12px;color:#6b7280">'+
            '<span>👨 男'+m.male+'</span><span>👩 女'+m.female+'</span>'+
            '<span>🏢 '+m.bureau_count+'个路局</span></div></div></div>';
    });
    html+='</div>';
    document.getElementById('dataList').innerHTML=html;
}
function showMajorDetail(name){
    const m=data.majors.find(x=>x.name===name);
    if(!m)return;
    document.getElementById('modalTitle').textContent='📖 '+m.name;
    let html='<div class="info-line"><span class="ilabel">招录总人数</span><span class="ivalue" style="color:#2563eb;font-size:18px">'+m.total+'</span></div>'+
        '<div class="info-line"><span class="ilabel">男生</span><span class="ivalue">'+m.male+' ('+m.male_pct+')</span></div>'+
        '<div class="info-line"><span class="ilabel">女生</span><span class="ivalue">'+m.female+' ('+m.female_pct+')</span></div>'+
        '<div class="info-line"><span class="ilabel">覆盖路局</span><span class="ivalue">'+m.bureau_count+'个</span></div>'+
        '<div style="margin-top:12px"><div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:8px">各路局招录详情：</div>'+
        '<table style="width:100%;border-collapse:collapse;font-size:13px">'+
        '<thead><tr style="background:#f3f4f6;border-bottom:2px solid #e5e7eb">'+
        '<th style="padding:8px 10px;text-align:left;color:#374151;font-weight:600">路局</th>'+
        '<th style="padding:8px 10px;text-align:center;color:#374151;font-weight:600">总计</th>'+
        '<th style="padding:8px 10px;text-align:center;color:#374151;font-weight:600">男生</th>'+
        '<th style="padding:8px 10px;text-align:center;color:#374151;font-weight:600">女生</th></tr></thead><tbody>';
    m.bureau_details.forEach(d=>{
        html+='<tr style="border-bottom:1px solid #f3f4f6">'+
            '<td style="padding:8px 10px;color:#374151">'+d.name+'</td>'+
            '<td style="padding:8px 10px;text-align:center;font-weight:600;color:#2563eb">'+d.total+'</td>'+
            '<td style="padding:8px 10px;text-align:center;color:#6b7280">'+d.male+'</td>'+
            '<td style="padding:8px 10px;text-align:center;color:#6b7280">'+d.female+'</td></tr>';
    });
    html+='</tbody></table></div>';
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