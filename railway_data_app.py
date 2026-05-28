"""铁路招录数据查询 - 服务端渲染，不依赖 JS 执行生成内容"""
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

def render_bureau_section(data):
    """服务端渲染按路局视图的完整HTML"""
    bureaus = data["bureaus"]
    grand = data["grand_total"]
    total_b = data["total_bureaus"]
    total_m = data["total_majors"]

    cards = []
    idx = 0
    for b in bureaus:
        if b["total"]["total"] == 0:
            continue  # 跳过郑州局等空数据
        idx += 1
        name = b["name"]
        t = b["total"]
        total_num = t["total"]
        male = t["male"]
        female = t["female"]
        major_count = len(b["majors"])

        majors_html = ""
        for m in b["majors"]:
            mn = m["name"]
            mm = m["male"]
            mf = m["female"]
            mt = m["total"]
            mp = m.get("male_pct", "0%")
            fp = m.get("female_pct", "0%")
            majors_html += f"""<div class="major-row"><span class="mname">{mn}</span><span class="mcount">{mt}人</span><span class="mbreakdown">♂{mm} {mp} ♀{mf} {fp}</span></div>"""

        if female == 0 and male == 0:
            gender = f"共{total_num}人"
        else:
            gender = f"♂{male}人 ♀{female}人"

        cards.append(f"""<div class="bureau-card" onclick="toggleCard(this)" data-index="{idx}">
  <div class="card-header">
    <span class="name">{name}</span>
    <span><span class="total">{total_num}<small>人</small></span><span class="arrow">▾</span></span>
  </div>
  <div class="card-stats"><span>{major_count}个专业</span><span>{gender}</span></div>
  <div class="card-detail">{majors_html}</div>
</div>""")

    cards_html = "\n".join(cards)

    return f"""<div class="stats-row">
  <div class="stat-card"><div class="num">{total_b}</div><div class="label">铁路局</div></div>
  <div class="stat-card"><div class="num">{total_m}</div><div class="label">专业</div></div>
  <div class="stat-card"><div class="num">{grand}</div><div class="label">招录总数</div></div>
</div>
<div id="bureauGrid" class="bureau-grid">{cards_html}</div>"""

def render_major_section(data):
    """服务端渲染按专业视图的完整HTML"""
    majors = data["majors"]
    cards = []
    for m in majors:
        name = m["name"]
        total = m["total"]
        male = m["male"]
        female = m["female"]
        mp = m["male_pct"]
        fp = m["female_pct"]
        bc = m["bureau_count"]
        blist = m.get("bureaus", [])

        # 生成路局标签
        chips = "".join(f'<span class="bureau-chip">{b}</span>' for b in blist)

        cards.append(f"""<div class="major-card" onclick="showMajorDetail(this)" data-name="{name}">
  <div class="card-header">
    <span class="name">{name}</span>
    <span class="total">{total}<small>人</small></span>
  </div>
  <div class="card-stats"><span>{bc}个路局</span><span>♂{male} {mp} ♀{female} {fp}</span></div>
  <div class="card-tags">{chips}</div>
</div>""")

    cards_html = "\n".join(cards)

    return f"""<div class="stats-row">
  <div class="stat-card"><div class="num">{len(majors)}</div><div class="label">专业</div></div>
  <div class="stat-card"><div class="num">{data["grand_total"]}</div><div class="label">招录总数</div></div>
</div>
<div id="majorGrid" class="major-grid">{cards_html}</div>"""

def build_page():
    data = RAILWAY_DATA
    bureau_html = render_bureau_section(data)
    major_html = render_major_section(data)

    # 将 majors 数据构建为 JS 可用的 bureau_details 查找表
    majors_json = json.dumps(data["majors"], ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2025铁路局招录数据查询</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif;
    background: #f0f2f5;
    color: #1f2937;
    min-height: 100vh;
}}
.header {{
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    color: white;
    padding: 20px 16px 16px;
    text-align: center;
}}
.header h1 {{ font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
.header .sub {{ font-size: 13px; color: rgba(255,255,255,0.7); }}
.notice {{
    background: #fef3c7;
    color: #92400e;
    text-align: center;
    padding: 10px 16px;
    font-size: 13px;
    border-bottom: 1px solid #fde68a;
}}
.tabs {{
    display: flex;
    background: white;
    border-bottom: 1px solid #e5e7eb;
    position: sticky;
    top: 0;
    z-index: 10;
}}
.tab {{
    flex: 1;
    text-align: center;
    padding: 14px 8px;
    font-size: 15px;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
}}
.tab.active {{ color: #2563eb; border-bottom-color: #2563eb; }}
.tab .badge {{
    display: inline-block;
    background: #e5e7eb;
    color: #6b7280;
    font-size: 11px;
    padding: 1px 8px;
    border-radius: 10px;
    margin-left: 4px;
}}
.tab.active .badge {{ background: #dbeafe; color: #2563eb; }}
.search-bar {{
    padding: 12px 16px;
    background: white;
}}
.search-bar input {{
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}}
.search-bar input:focus {{ border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }}
.content {{
    max-width: 800px;
    margin: 0 auto;
    padding: 12px 12px 80px;
}}
.stats-row {{
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}}
.stat-card {{
    flex: 1;
    background: white;
    border-radius: 12px;
    padding: 14px 12px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}
.stat-card .num {{ font-size: 24px; font-weight: 700; color: #2563eb; }}
.stat-card .label {{ font-size: 12px; color: #6b7280; margin-top: 2px; }}
.bureau-grid, .major-grid {{ display: flex; flex-direction: column; gap: 8px; }}
.major-grid {{ display: none; }}
.bureau-card, .major-card {{
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: all 0.2s;
    cursor: pointer;
}}
.bureau-card:hover, .major-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
.bureau-card .card-header, .major-card .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
}}
.card-header .name {{ font-size: 16px; font-weight: 600; }}
.card-header .total {{ font-size: 18px; font-weight: 700; color: #2563eb; }}
.card-header .total small {{ font-size: 12px; font-weight: 400; color: #6b7280; }}
.card-header .arrow {{ color: #9ca3af; font-size: 18px; margin-left: 8px; transition: transform 0.2s; }}
.bureau-card.expanded .card-header .arrow {{ transform: rotate(180deg); }}
.card-stats {{
    display: flex;
    justify-content: space-between;
    padding: 0 16px 10px;
    font-size: 13px;
    color: #6b7280;
}}
.card-tags {{ padding: 0 16px 12px; }}
.bureau-card .card-detail {{ display: none; border-top: 1px solid #f3f4f6; padding: 8px 16px 12px; }}
.bureau-card.expanded .card-detail {{ display: block; }}
.bureau-card .major-row {{
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    font-size: 14px;
    border-bottom: 1px solid #f9fafb;
}}
.bureau-card .major-row:last-child {{ border-bottom: none; }}
.bureau-card .major-row .mname {{ color: #374151; flex: 1; }}
.bureau-card .major-row .mcount {{ font-weight: 600; color: #2563eb; width: 50px; text-align: right; }}
.bureau-card .major-row .mbreakdown {{ color: #9ca3af; font-size: 12px; width: 130px; text-align: right; }}
.backdrop {{
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 20;
    justify-content: center;
    align-items: flex-start;
    padding-top: 40px;
}}
.modal {{
    background: white;
    border-radius: 20px;
    width: 90%;
    max-width: 480px;
    max-height: 80vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}}
.modal-header {{
    padding: 16px 20px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.modal-header h2 {{ font-size: 18px; font-weight: 600; }}
.modal-header .close {{ width: 32px; height: 32px; border-radius: 50%; border: none; background: #f3f4f6; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
.modal-body {{ padding: 12px 20px 20px; overflow-y: auto; flex: 1; }}
.modal-body .info-line {{ display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px; border-bottom: 1px solid #f3f4f6; }}
.modal-body .info-line:last-child {{ border-bottom: none; }}
.modal-body .info-line .ilabel {{ color: #6b7280; }}
.modal-body .info-line .ivalue {{ font-weight: 600; }}
.bureau-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }}
.bureau-table th {{ background: #f8fafc; padding: 8px 6px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb; }}
.bureau-table td {{ padding: 7px 6px; border-bottom: 1px solid #f3f4f6; }}
.bureau-table tr:hover td {{ background: #fafafa; }}
.bureau-table .num {{ text-align: center; }}
.bureau-chip {{ display: inline-block; background: #eff6ff; color: #2563eb; font-size: 12px; padding: 2px 10px; border-radius: 12px; margin: 2px 3px; }}
.summary {{
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: white;
    border-top: 1px solid #e5e7eb;
    padding: 10px 16px;
    text-align: center;
    font-size: 12px;
    color: #9ca3af;
    z-index: 5;
}}
</style>
</head>
<body>
<div class="header">
    <h1>🚂 2025级 铁路局招录数据</h1>
    <div class="sub">湖南铁道职业技术学院（东校区）</div>
</div>
<div class="notice">📢 温馨提示：所有招录数据均来自中国铁路人才招聘网的官方公示</div>
<div class="tabs">
    <div class="tab active" onclick="switchTab('bureau',this)">🏢 按路局 <span class="badge">{data["total_bureaus"]}</span></div>
    <div class="tab" onclick="switchTab('major',this)">📚 按专业 <span class="badge">{data["total_majors"]}</span></div>
</div>
<div class="search-bar"><input type="text" id="searchInput" placeholder="🔍 搜索路局或专业名称..." oninput="filterData()"></div>
<div class="content" id="contentArea">
    <div id="tabBureau">{bureau_html}</div>
    <div id="tabMajor" style="display:none">{major_html}</div>
</div>
<div class="summary">🏢 {data["total_bureaus"]}家铁路局 · 📚 {data["total_majors"]}个专业 · 👥 共{data["grand_total"]}人</div>
<div class="backdrop" id="modalBackdrop" onclick="closeModal()">
    <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-header"><h2 id="modalTitle">详情</h2><button class="close" onclick="closeModal()">✕</button></div>
        <div class="modal-body" id="modalBody"></div>
    </div>
</div>
<script>
const MAJORS_DATA = {majors_json};

function switchTab(tab, el) {{
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tabBureau').style.display = tab==='bureau' ? '' : 'none';
    document.getElementById('tabMajor').style.display = tab==='major' ? '' : 'none';
}}

function toggleCard(el) {{
    el.classList.toggle('expanded');
}}

function filterData() {{
    const q = document.getElementById('searchInput').value.trim().toLowerCase();
    // 过滤路局卡片
    document.querySelectorAll('#tabBureau .bureau-card').forEach(c=>{{
        const name = c.querySelector('.name').textContent.toLowerCase();
        c.style.display = name.includes(q) ? '' : 'none';
    }});
    // 过滤专业卡片
    document.querySelectorAll('#tabMajor .major-card').forEach(c=>{{
        const name = c.getAttribute('data-name').toLowerCase();
        c.style.display = name.includes(q) ? '' : 'none';
    }});
}}

function showMajorDetail(el) {{
    const name = el.getAttribute('data-name');
    const m = MAJORS_DATA.find(x=>x.name===name);
    if (!m) return;
    let html = '<div class="info-line"><span class="ilabel">招录总数</span><span class="ivalue">'+m.total+'人</span></div>';
    html += '<div class="info-line"><span class="ilabel">男生</span><span class="ivalue">'+m.male+'人 ('+m.male_pct+')</span></div>';
    html += '<div class="info-line"><span class="ilabel">女生</span><span class="ivalue">'+m.female+'人 ('+m.female_pct+')</span></div>';
    html += '<div class="info-line"><span class="ilabel">涉及路局</span><span class="ivalue">'+m.bureau_count+'家</span></div>';
    html += '<br><table class="bureau-table"><thead><tr><th>路局</th><th class="num">♂</th><th class="num">♀</th><th class="num">合计</th></tr></thead><tbody>';
    for (const d of m.bureau_details) {{
        html += '<tr><td>'+d.name+'</td><td class="num">'+d.male+'</td><td class="num">'+d.female+'</td><td class="num"><b>'+d.total+'</b></td></tr>';
    }}
    html += '</tbody></table>';
    document.getElementById('modalTitle').textContent = name;
    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('modalBackdrop').style.display = 'flex';
}}

function closeModal() {{
    document.getElementById('modalBackdrop').style.display = 'none';
}}
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return build_page()

@app.get("/api/data")
async def api_data():
    return RAILWAY_DATA