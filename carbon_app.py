"""万象归踪 — 铁路轮对踏面缺陷智能检测系统 (双碳版)"""
import json, os, math
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

def build_page():
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>万象归踪 — 轮对踏面缺陷智能检测系统</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;scroll-behavior:smooth}}
body{{font-family:'Noto Sans SC',sans-serif;background:#060d1a;color:#e2e8f0;overflow-x:hidden}}

/* === nav === */
nav{{position:fixed;top:0;width:100%;z-index:1000;padding:16px 40px;
  display:flex;justify-content:space-between;align-items:center;
  background:rgba(6,13,26,.85);backdrop-filter:blur(12px);border-bottom:1px solid rgba(96,165,250,.15)}}
.nav-logo{{font-size:18px;font-weight:700;background:linear-gradient(90deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.nav-links{{display:flex;gap:24px;list-style:none}}
.nav-links a{{color:#94a3b8;text-decoration:none;font-size:14px;transition:color .3s}}
.nav-links a:hover{{color:#60a5fa}}

/* === hero === */
.hero{{min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;
  text-align:center;padding:120px 20px 80px;position:relative;overflow:hidden}}
.hero-bg{{position:absolute;inset:0;background:
  radial-gradient(ellipse 600px 400px at 30% 50%,rgba(96,165,250,.12),transparent),
  radial-gradient(ellipse 500px 400px at 70% 60%,rgba(167,139,250,.1),transparent),
  radial-gradient(ellipse 300px 300px at 50% 20%,rgba(52,211,153,.06),transparent);
  pointer-events:none}}
.hero-tag{{display:inline-block;padding:6px 18px;border-radius:20px;font-size:12px;font-weight:500;
  background:rgba(52,211,153,.15);color:#34d399;border:1px solid rgba(52,211,153,.3);margin-bottom:24px;
  letter-spacing:1px}}
.hero h1{{font-size:clamp(32px,6vw,64px);font-weight:900;line-height:1.2;margin-bottom:16px}}
.hero h1 .gradient{{background:linear-gradient(135deg,#60a5fa 20%,#a78bfa 50%,#34d399 80%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero-sub{{font-size:clamp(16px,2.5vw,22px);color:#94a3b8;max-width:700px;margin-bottom:40px;line-height:1.6}}
.hero-actions{{display:flex;gap:16px;flex-wrap:wrap;justify-content:center}}
.btn-primary{{display:inline-flex;align-items:center;gap:8px;padding:14px 32px;border-radius:12px;
  font-size:15px;font-weight:600;text-decoration:none;cursor:pointer;transition:all .3s;
  background:linear-gradient(135deg,#60a5fa,#3b82f6);color:#fff;border:none;box-shadow:0 4px 20px rgba(96,165,250,.3)}}
.btn-primary:hover{{transform:translateY(-2px);box-shadow:0 8px 30px rgba(96,165,250,.4)}}
.btn-outline{{display:inline-flex;align-items:center;gap:8px;padding:14px 32px;border-radius:12px;
  font-size:15px;font-weight:600;text-decoration:none;cursor:pointer;transition:all .3s;
  background:transparent;color:#94a3b8;border:1px solid rgba(148,163,184,.3)}}
.btn-outline:hover{{border-color:#60a5fa;color:#60a5fa;transform:translateY(-2px)}}

/* === scroll indicator === */
.scroll-indicator{{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:6px;color:#64748b;font-size:12px;animation:bounce 2s infinite}}
@keyframes bounce{{0%,100%{{transform:translateX(-50%) translateY(0)}}50%{{transform:translateX(-50%) translateY(8px)}}}}

/* === sections === */
section{{padding:100px 20px}}
.section-inner{{max-width:1100px;margin:0 auto}}
.section-title{{text-align:center;margin-bottom:16px}}
.section-title h2{{font-size:clamp(24px,4vw,36px);font-weight:700}}
.section-title p{{color:#64748b;max-width:600px;margin:12px auto 0;font-size:15px;line-height:1.6}}
.section-divider{{width:60px;height:3px;background:linear-gradient(90deg,#60a5fa,#34d399);border-radius:2px;margin:16px auto 40px}}

/* === carbon data === */
.carbon-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-top:40px}}
.carbon-card{{background:linear-gradient(145deg,rgba(30,41,59,.6),rgba(15,23,42,.6));backdrop-filter:blur(10px);
  border-radius:16px;padding:28px;text-align:center;border:1px solid rgba(148,163,184,.1);transition:all .4s}}
.carbon-card:hover{{border-color:rgba(96,165,250,.3);transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.3)}}
.carbon-card .icon{{font-size:36px;margin-bottom:12px}}
.carbon-card .num{{font-size:32px;font-weight:700;background:linear-gradient(135deg,#60a5fa,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.carbon-card .label{{color:#94a3b8;font-size:13px;margin-top:6px}}
.carbon-card .sub-label{{color:#64748b;font-size:11px;margin-top:2px}}

/* === timeline === */
.timeline{{position:relative;padding-left:40px;margin-top:40px}}
.timeline::before{{content:'';position:absolute;left:15px;top:0;bottom:0;width:2px;background:linear-gradient(180deg,#60a5fa,#34d399,#a78bfa)}}
.tl-item{{position:relative;margin-bottom:36px;padding-left:30px}}
.tl-item::before{{content:'';position:absolute;left:-25px;top:5px;width:12px;height:12px;border-radius:50%;background:#60a5fa;border:3px solid #060d1a;box-shadow:0 0 0 2px #60a5fa}}
.tl-item:nth-child(2)::before{{background:#34d399;box-shadow:0 0 0 2px #34d399}}
.tl-item:nth-child(3)::before{{background:#a78bfa;box-shadow:0 0 0 2px #a78bfa}}
.tl-item h3{{font-size:16px;font-weight:600;margin-bottom:4px}}
.tl-item p{{color:#94a3b8;font-size:13px;line-height:1.6}}

/* === features === */
.features-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;margin-top:40px}}
.feature-card{{background:linear-gradient(145deg,rgba(30,41,59,.5),rgba(15,23,42,.5));border-radius:16px;padding:32px;
  border:1px solid rgba(148,163,184,.08);transition:all .4s;position:relative;overflow:hidden}}
.feature-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0}}
.feature-card:nth-child(1)::before{{background:linear-gradient(90deg,#60a5fa,#3b82f6)}}
.feature-card:nth-child(2)::before{{background:linear-gradient(90deg,#a78bfa,#8b5cf6)}}
.feature-card:nth-child(3)::before{{background:linear-gradient(90deg,#34d399,#10b981)}}
.feature-card:hover{{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.4);border-color:rgba(96,165,250,.2)}}
.feature-card .f-icon{{font-size:32px;margin-bottom:12px}}
.feature-card h3{{font-size:16px;font-weight:600;margin-bottom:8px}}
.feature-card p{{color:#94a3b8;font-size:13px;line-height:1.7}}

/* === data table === */
.data-comparison{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:40px}}
.dc-old,.dc-new{{padding:32px;border-radius:16px}}
.dc-old{{background:linear-gradient(145deg,rgba(239,68,68,.08),rgba(239,68,68,.03));border:1px solid rgba(239,68,68,.15)}}
.dc-new{{background:linear-gradient(145deg,rgba(52,211,153,.08),rgba(52,211,153,.03));border:1px solid rgba(52,211,153,.15)}}
.dc-title{{font-size:18px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.dc-old .dc-title{{color:#f87171}}
.dc-new .dc-title{{color:#34d399}}
.dc-item{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(148,163,184,.08);font-size:13px}}
.dc-item:last-child{{border:none}}
.dc-item .key{{color:#94a3b8}}
.dc-item .val{{font-weight:600}}

/* === team === */
.team-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-top:40px}}
.team-card{{text-align:center;padding:24px;background:rgba(30,41,59,.4);border-radius:16px;border:1px solid rgba(148,163,184,.08)}}
.team-card .avatar{{width:64px;height:64px;border-radius:50%;margin:0 auto 12px;
  background:linear-gradient(135deg,#60a5fa,#a78bfa);display:flex;align-items:center;justify-content:center;font-size:24px}}
.team-card h3{{font-size:15px;font-weight:600}}
.team-card p{{color:#94a3b8;font-size:12px;margin-top:4px}}

/* === footer === */
footer{{text-align:center;padding:40px;border-top:1px solid rgba(148,163,184,.08);color:#64748b;font-size:13px}}

/* === bar chart animation === */
.chart-bar{{display:flex;align-items:center;gap:12px;margin:8px 0}}
.chart-bar .label{{width:120px;font-size:13px;color:#94a3b8;text-align:right;flex-shrink:0}}
.chart-bar .track{{flex:1;height:20px;border-radius:10px;background:rgba(148,163,184,.1);overflow:hidden}}
.chart-bar .fill{{height:100%;border-radius:10px;transition:width 1.5s cubic-bezier(.4,0,.2,1);display:flex;align-items:center;justify-content:flex-end;padding-right:8px;font-size:11px;font-weight:600;color:#fff;min-width:30px}}
.fill-blue{{background:linear-gradient(90deg,#3b82f6,#60a5fa)}}
.fill-green{{background:linear-gradient(90deg,#10b981,#34d399)}}
.fill-purple{{background:linear-gradient(90deg,#8b5cf6,#a78bfa)}}

/* === gallery === */
.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:40px}}
.gallery-item{{aspect-ratio:4/3;border-radius:12px;overflow:hidden;background:rgba(30,41,59,.4);
  border:1px solid rgba(148,163,184,.08);display:flex;align-items:center;justify-content:center;
  font-size:40px;transition:all .4s}}
.gallery-item:hover{{border-color:rgba(96,165,250,.3);transform:scale(1.02)}}
.gallery-item .g-label{{font-size:12px;color:#94a3b8;text-align:center;padding:8px}}

@media(max-width:768px){{
  nav{{padding:12px 16px}}
  .nav-links{{gap:12px;font-size:12px}}
  .nav-links a{{font-size:12px}}
  .hero{{padding:100px 16px 60px}}
  section{{padding:60px 16px}}
  .data-comparison{{grid-template-columns:1fr}}
  .chart-bar .label{{width:80px;font-size:11px}}
  .carbon-grid{{grid-template-columns:repeat(2,1fr)}}
  .features-grid{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>

<nav>
  <div class="nav-logo">🚂 万象归踪</div>
  <ul class="nav-links">
    <li><a href="#carbon">碳减排</a></li>
    <li><a href="#tech">技术</a></li>
    <li><a href="#compare">对比</a></li>
    <li><a href="#team">团队</a></li>
  </ul>
</nav>

<!-- Hero -->
<section class="hero" id="home">
  <div class="hero-bg"></div>
  <div class="hero-tag">🌱 双碳减排 · 铁路先行</div>
  <h1><span class="gradient">万象归踪</span></h1>
  <p class="hero-sub">基于AI深度学习与轨边双向阵列成像的<br>轮对踏面缺陷智能检测系统<br><span style="color:#34d399;font-size:14px">以智能检测驱动铁路低碳运维</span></p>
  <div class="hero-actions">
    <a href="#carbon" class="btn-primary">📊 碳减排成果</a>
    <a href="#tech" class="btn-outline">🔬 技术方案</a>
  </div>
  <div class="scroll-indicator">
    <span>向下滚动</span>
    <span>↓</span>
  </div>
</section>

<!-- Carbon Data -->
<section id="carbon">
<div class="section-inner">
  <div class="section-title">
    <h2>🌱 双碳减排 · 核心数据</h2>
    <p>智能检测替代传统人工检修，大幅降低铁路运维过程中的能源消耗与碳排放</p>
  </div>
  <div class="section-divider"></div>
  <div class="carbon-grid">
    <div class="carbon-card">
      <div class="icon">⚡</div>
      <div class="num">92%</div>
      <div class="label">停车检测能耗降低</div>
      <div class="sub-label">边运营边检测，无需停车入库</div>
    </div>
    <div class="carbon-card">
      <div class="icon">🌲</div>
      <div class="num">12,600</div>
      <div class="label">年减排CO₂（吨）</div>
      <div class="sub-label">相当于种树 70 万棵</div>
    </div>
    <div class="carbon-card">
      <div class="icon">⏱</div>
      <div class="num">96%</div>
      <div class="label">检测效率提升</div>
      <div class="sub-label">30分钟→秒级，能耗指数级下降</div>
    </div>
    <div class="carbon-card">
      <div class="icon">👷</div>
      <div class="num">60%</div>
      <div class="label">人力消耗降低</div>
      <div class="sub-label">12人三班倒→5人监控，减少碳足迹</div>
    </div>
  </div>

  <div class="section-title" style="margin-top:60px">
    <h3 style="font-size:20px;font-weight:600">📉 碳排放对比</h3>
  </div>
  <div style="margin-top:24px">
    <div class="chart-bar">
      <div class="label">传统检测</div>
      <div class="track"><div class="fill fill-blue" style="width:100%">100%</div></div>
    </div>
    <div class="chart-bar">
      <div class="label">智能检测</div>
      <div class="track"><div class="fill fill-green" style="width:8%">8%</div></div>
    </div>
    <div class="chart-bar">
      <div class="label">减排效果</div>
      <div class="track"><div class="fill fill-purple" style="width:92%">92%↓</div></div>
    </div>
  </div>

  <div style="margin-top:40px;background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.15);border-radius:16px;padding:28px">
    <h4 style="font-size:15px;font-weight:600;color:#34d399;margin-bottom:12px">💡 碳减排机理</h4>
    <p style="color:#94a3b8;font-size:13px;line-height:1.8">
      传统轮对检测需将列车停运入库，单节车厢平均停车30分钟，配套照明、通风、检测设备持续耗电。<br>
      <strong>万象归踪</strong> 采用<strong>轨边双向阵列成像</strong>技术，实现列车<strong>"边运营边检测"</strong>：<br>
      ① 消除停车入库能耗 → 单节车厢每次减少约 45kg CO₂排放<br>
      ② 减少维修车间照明/空调使用 → 年减少约 1800吨 CO₂<br>
      ③ 优化维修计划、减少非必要检修 → 降低备件生产碳排放约 3800吨 CO₂<br>
      ④ 全年应用预计减排 <strong style="color:#34d399">12,600 吨 CO₂</strong>，相当于 70 万棵树的年碳吸收量
    </p>
  </div>
</div>
</section>

<!-- Tech -->
<section id="tech" style="background:rgba(96,165,250,.02)">
<div class="section-inner">
  <div class="section-title">
    <h2>🔬 技术方案</h2>
    <p>基于改进型YOLO深度学习算法 + 轨边双向阵列成像，实现端到端智能化检测</p>
  </div>
  <div class="section-divider"></div>
  <div class="features-grid">
    <div class="feature-card">
      <div class="f-icon">🧠</div>
      <h3>注意力增强机制</h3>
      <p>引入注意力模块，小目标缺陷检测精度提升16.4%；消除光照不均、表面污渍等复杂环境影响，提高检测稳定性。mAP提高13.2%，召回率提高16.4%</p>
    </div>
    <div class="feature-card">
      <div class="f-icon">📦</div>
      <h3>轻量化模型设计</h3>
      <p>引入GhostNet卷积模块，模型体积从35MB压缩至10MB以内（↓71.4%），适配终端部署设备算力限制，降低边缘计算设备功耗，间接减少碳排放</p>
    </div>
    <div class="feature-card">
      <div class="f-icon">🛤️</div>
      <h3>轨边双向阵列 + 5G传输</h3>
      <p>轨边双向阵列布局突破运行轮对遮挡难题，借助5T信号机房实现检测结果实时存储和远端可视化；每秒近百帧采集、分级报警，实现"边运营边检测"</p>
    </div>
  </div>

  <!-- Timeline -->
  <div class="section-title" style="margin-top:40px">
    <h3 style="font-size:20px;font-weight:600">📅 研发历程</h3>
  </div>
  <div class="timeline">
    <div class="tl-item">
      <h3>2024.10 — 团队成立 · 方向确立</h3>
      <p>组建"万象归踪"团队，确定轮对踏面缺陷AI视觉检测研究方向，选用YOLO检测模型</p>
    </div>
    <div class="tl-item">
      <h3>2024.11-12 — 行业调研 · 痛点挖掘</h3>
      <p>前往株洲车辆段等铁路企业实地调研，发现传统检测高能耗、低效率痛点</p>
    </div>
    <div class="tl-item">
      <h3>2025.03-04 — 算法突破 · 专利布局</h3>
      <p>改进型YOLO算法识别率突破94%，申报2项实用新型专利、3项软著，构建技术壁垒</p>
    </div>
    <div class="tl-item">
      <h3>2025.11-12 — 型式试验 · 减碳验证</h3>
      <p>开展型式试验，各项参数符合标准；联合北京新联铁集团进行碳排放对比验证</p>
    </div>
  </div>
</div>
</section>

<!-- Comparison -->
<section id="compare">
<div class="section-inner">
  <div class="section-title">
    <h2>⚖️ 传统 vs 智能 检测对比</h2>
    <p>从能耗、效率、人力、碳排放四个维度全面对比</p>
  </div>
  <div class="section-divider"></div>
  <div class="data-comparison">
    <div class="dc-old">
      <div class="dc-title">❌ 传统检测方式</div>
      <div class="dc-item"><span class="key">检测方式</span><span class="val">停车入库，人工目视</span></div>
      <div class="dc-item"><span class="key">单节耗时</span><span class="val">30-60分钟</span></div>
      <div class="dc-item"><span class="key">人员配置</span><span class="val">12人三班倒</span></div>
      <div class="dc-item"><span class="key">单次能耗</span><span class="val">45kg CO₂/节</span></div>
      <div class="dc-item"><span class="key">漏检率</span><span class="val">~15%（人工疲劳）</span></div>
      <div class="dc-item"><span class="key">年碳排</span><span class="val" style="color:#f87171">13,700吨</span></div>
    </div>
    <div class="dc-new">
      <div class="dc-title">✅ 万象归踪智能检测</div>
      <div class="dc-item"><span class="key">检测方式</span><span class="val">轨边阵列，边运营边检</span></div>
      <div class="dc-item"><span class="key">单节耗时</span><span class="val">秒级（近百帧/秒）</span></div>
      <div class="dc-item"><span class="key">人员配置</span><span class="val">5人（3监控+2复核）</span></div>
      <div class="dc-item"><span class="key">单次能耗</span><span class="val">~3.6kg CO₂/节</span></div>
      <div class="dc-item"><span class="key">漏检率</span><span class="val">~5%（AI持续稳定）</span></div>
      <div class="dc-item"><span class="key">年碳排</span><span class="val" style="color:#34d399">1,100吨</span></div>
    </div>
  </div>
  <p style="text-align:center;margin-top:20px;color:#64748b;font-size:13px">
    🎯 年减排 <strong style="color:#34d399">12,600 吨 CO₂</strong> | 效率提升 <strong style="color:#60a5fa">96%</strong> | 人力降低 <strong style="color:#a78bfa">60%</strong>
  </p>
</div>
</section>

<!-- Platform -->
<section id="platform" style="background:rgba(167,139,250,.02)">
<div class="section-inner">
  <div class="section-title">
    <h2>🏗️ 平台资源</h2>
    <p>多平台资源支撑，让技术从实验室走向产业</p>
  </div>
  <div class="section-divider"></div>
  <div class="carbon-grid">
    <div class="carbon-card">
      <div class="icon">🔬</div>
      <div class="num">刘友梅</div>
      <div class="label">院士工作站指导</div>
      <div class="sub-label">算法模型研究支持</div>
    </div>
    <div class="carbon-card">
      <div class="icon">🏭</div>
      <div class="num">新联铁</div>
      <div class="label">集团合作</div>
      <div class="sub-label">样品装车实验 · 碳数据采集</div>
    </div>
    <div class="carbon-card">
      <div class="icon">🚀</div>
      <div class="num">5万</div>
      <div class="label">启动资金</div>
      <div class="sub-label">株洲双创精英人才政策</div>
    </div>
    <div class="carbon-card">
      <div class="icon">🎓</div>
      <div class="num">双基地</div>
      <div class="label">创新创业+轨道仿真</div>
      <div class="sub-label">省级孵化基地 + 国家级虚拟仿真</div>
    </div>
  </div>
</div>
</section>

<!-- Team -->
<section id="team">
<div class="section-inner">
  <div class="section-title">
    <h2>👥 团队介绍</h2>
    <p>轨交安全梦之队 · 匠心+应用+创新</p>
  </div>
  <div class="section-divider"></div>
  <div class="team-grid">
    <div class="team-card">
      <div class="avatar">👤</div>
      <h3>齐财熔</h3>
      <p>项目负责人</p>
    </div>
    <div class="team-card">
      <div class="avatar">👤</div>
      <h3>技术团队</h3>
      <p>算法研发 · 模型训练</p>
    </div>
    <div class="team-card">
      <div class="avatar">👤</div>
      <h3>张峰嘉</h3>
      <p>全国铁路技能大师<br>全国五一劳动奖章</p>
    </div>
    <div class="team-card">
      <div class="avatar">👤</div>
      <h3>刘友梅院士</h3>
      <p>院士工作站指导</p>
    </div>
  </div>
</div>
</section>

<!-- Product Gallery -->
<section style="background:rgba(96,165,250,.02)">
<div class="section-inner">
  <div class="section-title">
    <h2>📸 产品展示</h2>
    <p>从实验室到轨边的全流程展示</p>
  </div>
  <div class="section-divider"></div>
  <div class="gallery">
    <div class="gallery-item">
      <div class="g-label">⚙️ 轨边阵列<br><span style="color:#64748b">双向成像布局</span></div>
    </div>
    <div class="gallery-item">
      <div class="g-label">🧠 AI缺陷识别<br><span style="color:#64748b">YOLO深度学习</span></div>
    </div>
    <div class="gallery-item">
      <div class="g-label">📊 数据分析<br><span style="color:#64748b">碳减排追踪</span></div>
    </div>
    <div class="gallery-item">
      <div class="g-label">🏭 现场试验<br><span style="color:#64748b">株洲车辆段</span></div>
    </div>
  </div>
</div>
</section>

<!-- Footer -->
<footer>
  <p>🚂 万象归踪 — 铁路轮对踏面缺陷智能检测系统</p>
  <p style="margin-top:4px">湖南铁道职业技术学院 · 中国国际大学生创新大赛</p>
  <p style="margin-top:8px;font-size:12px">© 2025 万象归踪团队 | 以智能检测驱动铁路低碳运维</p>
</footer>

<!-- Tracking -->
<script>
(function(){{
  if(window.__tracked) return; window.__tracked=true;
  try{{navigator.sendBeacon('/api/track',JSON.stringify({{
    p:'/carbon',r:document.referrer||'',t:navigator.userAgent||''
  }}))}}catch(e){{}}
}})();
</script>
</body>
</html>""")


@app.get("/")
def index():
    return build_page()