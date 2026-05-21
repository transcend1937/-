"""铁路就业题库 Web 应用 - FastAPI 后端"""

import json
import random
import logging
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from exam.questions import QUESTIONS

logger = logging.getLogger(__name__)

app = FastAPI(title="铁路就业题库")

CATEGORY_MAP = {
    "行测": "行测",
    "专业": "专业",
    "情景模拟": "情景模拟",
    "性格测试": "性格测试",
}

TYPE_MAP = {}
for q in QUESTIONS:
    t = q["type"]
    c = q["category"]
    if c not in TYPE_MAP:
        TYPE_MAP[c] = []
    if t not in TYPE_MAP[c]:
        TYPE_MAP[c].append(t)


@app.get("/api/categories")
def get_categories():
    """获取所有题型分类及子类型"""
    result = {}
    for cat, types in TYPE_MAP.items():
        result[cat] = {
            "types": types,
            "count": sum(1 for q in QUESTIONS if q["category"] == cat)
        }
    return {"code": 0, "data": result}


@app.get("/api/questions")
def get_questions(
    category: str = Query(None, description="题目大类"),
    type_name: str = Query(None, alias="type", description="具体题型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """获取题目列表（分页）"""
    filtered = QUESTIONS
    if category and category in CATEGORY_MAP:
        filtered = [q for q in filtered if q["category"] == category]
    if type_name:
        filtered = [q for q in filtered if q["type"] == type_name]

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    # 返回时隐藏答案（前端判题用）
    for item in items:
        item = dict(item)

    return {
        "code": 0,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    }


@app.get("/api/questions/random")
def get_random_questions(
    category: str = Query(None, description="题目大类"),
    type_name: str = Query(None, alias="type", description="具体题型"),
    count: int = Query(10, ge=1, le=30),
):
    """随机抽取题目"""
    filtered = QUESTIONS
    if category and category in CATEGORY_MAP:
        filtered = [q for q in filtered if q["category"] == category]
    if type_name:
        filtered = [q for q in filtered if q["type"] == type_name]

    if not filtered:
        return {"code": 0, "data": {"items": []}}

    selected = random.sample(filtered, min(count, len(filtered)))
    return {
        "code": 0,
        "data": {
            "total": len(selected),
            "items": selected,
        }
    }


@app.get("/api/questions/{question_id}")
def get_question(question_id: int):
    """获取单道题详情"""
    for q in QUESTIONS:
        if q["id"] == question_id:
            return {"code": 0, "data": q}
    raise HTTPException(status_code=404, detail="题目不存在")


class SubmitRequest(BaseModel):
    question_id: int
    selected: str


@app.post("/api/submit")
def submit_answer(req: SubmitRequest):
    """提交答案并返回判题结果"""
    for q in QUESTIONS:
        if q["id"] == req.question_id:
            is_correct = req.selected == q["answer"]
            return {
                "code": 0,
                "data": {
                    "correct": is_correct,
                    "answer": q["answer"],
                    "analysis": q["analysis"],
                }
            }
    raise HTTPException(status_code=404, detail="题目不存在")


class WrongAnswerRequest(BaseModel):
    question_id: int
    selected: str


@app.post("/api/wrong-answer")
def record_wrong_answer(req: WrongAnswerRequest):
    """记录错题（错题本功能）"""
    for q in QUESTIONS:
        if q["id"] == req.question_id:
            return {
                "code": 0,
                "data": {
                    "recorded": True,
                    "question_id": req.question_id,
                    "correct_answer": q["answer"],
                }
            }
    raise HTTPException(status_code=404, detail="题目不存在")


@app.get("/api/daily")
def daily_practice():
    """每日一练：随机抽取8道题，覆盖行测+专业"""
    import random
    xingce = [q for q in QUESTIONS if q["category"] == "行测"]
    zhuanye = [q for q in QUESTIONS if q["category"] == "专业"]
    daily = random.sample(xingce, min(4, len(xingce)))
    daily += random.sample(zhuanye, min(4, len(zhuanye)))
    random.shuffle(daily)
    return {
        "code": 0,
        "data": {
            "total": len(daily),
            "items": daily,
        }
    }


# 前端页面
EXAM_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>铁路就业题库 - 刷题练习</title>
    <style>
        /* ===== Reset & Base ===== */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: #f0f2f5;
            color: #333;
            min-height: 100vh;
        }

        /* ===== Header ===== */
        .header {
            background: linear-gradient(135deg, #1a73e8, #0d47a1);
            color: #fff;
            padding: 0 24px;
            height: 56px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        .header-title {
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header-title .icon { font-size: 22px; }
        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 14px;
        }
        .timer {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 12px;
            font-variant-numeric: tabular-nums;
        }
        .progress-text {
            font-weight: 500;
        }

        /* ===== Layout ===== */
        .layout {
            display: flex;
            padding-top: 56px;
            min-height: 100vh;
        }

        /* ===== Sidebar ===== */
        .sidebar {
            width: 220px;
            background: #fff;
            border-right: 1px solid #e8e8e8;
            padding: 20px 0;
            position: fixed;
            top: 56px;
            left: 0;
            bottom: 0;
            overflow-y: auto;
            z-index: 50;
        }
        .sidebar-section { margin-bottom: 8px; }
        .sidebar-title {
            padding: 8px 20px;
            font-size: 12px;
            font-weight: 600;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .sidebar-item {
            padding: 10px 20px 10px 24px;
            cursor: pointer;
            font-size: 14px;
            color: #555;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        .sidebar-item:hover {
            background: #f5f7fa;
            color: #1a73e8;
        }
        .sidebar-item.active {
            background: #e8f0fe;
            color: #1a73e8;
            border-left-color: #1a73e8;
            font-weight: 600;
        }
        .sidebar-item .count-badge {
            background: #e8e8e8;
            color: #666;
            font-size: 11px;
            padding: 1px 8px;
            border-radius: 10px;
        }
        .sidebar-item.active .count-badge {
            background: #1a73e8;
            color: #fff;
        }

        /* ===== Main Content ===== */
        .main-content {
            flex: 1;
            margin-left: 220px;
            padding: 24px;
            max-width: 860px;
        }

        /* ===== Category Nav (Mobile) ===== */
        .mobile-category-nav {
            display: none;
            background: #fff;
            padding: 12px 16px;
            overflow-x: auto;
            white-space: nowrap;
            border-bottom: 1px solid #e8e8e8;
            position: sticky;
            top: 56px;
            z-index: 60;
        }
        .mobile-category-nav .cat-btn {
            display: inline-block;
            padding: 6px 16px;
            margin-right: 8px;
            border-radius: 16px;
            font-size: 13px;
            cursor: pointer;
            border: 1px solid #ddd;
            background: #fff;
            color: #555;
            transition: all 0.2s;
        }
        .mobile-category-nav .cat-btn.active {
            background: #1a73e8;
            color: #fff;
            border-color: #1a73e8;
        }

        /* ===== Question Card ===== */
        .question-card {
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            padding: 28px;
            margin-bottom: 20px;
        }

        .question-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 8px;
        }
        .question-number {
            font-size: 14px;
            color: #888;
            font-weight: 500;
        }
        .question-number .num {
            color: #1a73e8;
            font-weight: 700;
            font-size: 16px;
        }
        .question-type-badge {
            font-size: 12px;
            padding: 3px 12px;
            border-radius: 12px;
            background: #e8f0fe;
            color: #1a73e8;
            font-weight: 500;
        }

        .question-text {
            font-size: 16px;
            line-height: 1.8;
            margin-bottom: 24px;
            color: #222;
            white-space: pre-wrap;
        }

        /* ===== Options ===== */
        .options-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .option-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 14px 18px;
            border: 2px solid #e8e8e8;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 15px;
            line-height: 1.6;
        }
        .option-item:hover {
            border-color: #90caf9;
            background: #f5f9ff;
        }
        .option-item .label {
            flex-shrink: 0;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #f0f2f5;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
            color: #555;
            transition: all 0.2s;
        }
        .option-item.selected {
            border-color: #1a73e8;
            background: #e8f0fe;
        }
        .option-item.selected .label {
            background: #1a73e8;
            color: #fff;
        }
        .option-item.correct {
            border-color: #34a853;
            background: #e6f4ea;
        }
        .option-item.correct .label {
            background: #34a853;
            color: #fff;
        }
        .option-item.wrong {
            border-color: #ea4335;
            background: #fce8e6;
        }
        .option-item.wrong .label {
            background: #ea4335;
            color: #fff;
        }
        .option-item.disabled {
            cursor: default;
            opacity: 0.85;
        }
        .option-item .option-text { flex: 1; padding-top: 2px; }

        /* ===== Analysis ===== */
        .analysis-box {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            background: #f8f9fe;
            border: 1px solid #e3e8f5;
            display: none;
        }
        .analysis-box.show { display: block; }
        .analysis-box .result-badge {
            display: inline-block;
            padding: 4px 16px;
            border-radius: 16px;
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 12px;
        }
        .analysis-box .result-correct {
            background: #e6f4ea;
            color: #1e7e34;
        }
        .analysis-box .result-wrong {
            background: #fce8e6;
            color: #c62828;
        }
        .analysis-box .result-text {
            font-size: 15px;
            line-height: 1.8;
            color: #444;
        }
        .analysis-box .result-text strong {
            color: #1a73e8;
        }
        .analysis-box .correct-answer {
            font-size: 14px;
            color: #34a853;
            font-weight: 600;
            margin-bottom: 8px;
        }

        /* ===== Bottom Bar ===== */
        .bottom-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 28px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #1a73e8;
            color: #fff;
        }
        .btn-primary:hover { background: #1557b0; }
        .btn-primary:disabled { background: #a0c4f8; cursor: not-allowed; }
        .btn-success {
            background: #34a853;
            color: #fff;
        }
        .btn-success:hover { background: #2d9249; }
        .btn-outline {
            background: #fff;
            color: #555;
            border: 1px solid #ddd;
        }
        .btn-outline:hover { background: #f5f5f5; }
        .btn-outline:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-sm { padding: 6px 16px; font-size: 13px; }
        .nav-buttons {
            display: flex;
            gap: 8px;
        }

        /* ===== Answer Sheet ===== */
        .answer-sheet-toggle {
            position: fixed;
            right: 20px;
            bottom: 100px;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: #1a73e8;
            color: #fff;
            border: none;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(26,115,232,0.4);
            z-index: 90;
            transition: transform 0.2s;
        }
        .answer-sheet-toggle:hover { transform: scale(1.1); }

        .answer-sheet-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 200;
        }
        .answer-sheet-overlay.show { display: block; }

        .answer-sheet {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #fff;
            border-radius: 16px;
            padding: 28px;
            width: 90%;
            max-width: 480px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 210;
            display: none;
        }
        .answer-sheet.show { display: block; }
        .answer-sheet h3 {
            font-size: 18px;
            margin-bottom: 16px;
            color: #333;
        }
        .answer-sheet .stats {
            display: flex;
            gap: 24px;
            margin-bottom: 16px;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .answer-sheet .stats .stat-item {
            text-align: center;
        }
        .answer-sheet .stats .stat-item .num {
            font-size: 20px;
            font-weight: 700;
            color: #1a73e8;
        }
        .answer-sheet .stats .stat-item .label {
            font-size: 12px;
            color: #888;
        }
        .answer-sheet .stats .stat-item .num.correct-num { color: #34a853; }
        .answer-sheet .stats .stat-item .num.wrong-num { color: #ea4335; }

        .answer-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 8px;
        }
        .answer-grid .grid-item {
            width: 100%;
            aspect-ratio: 1;
            border-radius: 8px;
            border: 1px solid #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            background: #fff;
        }
        .answer-grid .grid-item:hover { border-color: #1a73e8; }
        .answer-grid .grid-item.current {
            border-color: #1a73e8;
            background: #e8f0fe;
            font-weight: 700;
        }
        .answer-grid .grid-item.answered {
            background: #e6f4ea;
            border-color: #34a853;
            color: #1e7e34;
        }
        .answer-grid .grid-item.answered-wrong {
            background: #fce8e6;
            border-color: #ea4335;
            color: #c62828;
        }

        .answer-sheet .close-btn {
            position: absolute;
            top: 12px;
            right: 16px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #888;
        }

        /* ===== Start Screen ===== */
        .start-screen {
            text-align: center;
            padding: 60px 20px;
        }
        .start-screen h2 {
            font-size: 24px;
            color: #1a73e8;
            margin-bottom: 12px;
        }
        .start-screen p {
            color: #888;
            margin-bottom: 24px;
            font-size: 15px;
        }
        .start-screen .start-options {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-width: 360px;
            margin: 0 auto;
        }
        .start-screen .start-options button {
            padding: 14px 24px;
            border: 2px solid #e8e8e8;
            border-radius: 12px;
            background: #fff;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .start-screen .start-options button:hover {
            border-color: #1a73e8;
            background: #f5f9ff;
        }

        /* ===== Empty State ===== */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state .big-icon { font-size: 48px; margin-bottom: 12px; }

        /* ===== Responsive ===== */
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .mobile-category-nav { display: flex; }
            .main-content {
                margin-left: 0;
                padding: 16px;
            }
            .question-card { padding: 20px; }
            .question-text { font-size: 15px; }
            .option-item { padding: 12px 14px; font-size: 14px; }
            .header-title { font-size: 16px; }
            .header { padding: 0 16px; }
        }
        @media (max-width: 480px) {
            .answer-grid { grid-template-columns: repeat(5, 1fr); }
            .nav-buttons .btn { padding: 8px 16px; font-size: 13px; }
            .question-header { flex-direction: column; align-items: flex-start; }
        }

        /* ===== Scrollbar ===== */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #aaa; }
    </style>
</head>
<body>

<!-- Header -->
<header class="header">
    <div class="header-title">
        <span class="icon">📝</span>
        <span>铁路就业题库</span>
    </div>
    <div class="header-right">
        <span class="timer" id="timer">00:00</span>
        <span class="progress-text" id="progressText">0/0</span>
    </div>
</header>

<!-- Mobile Category Nav -->
<div class="mobile-category-nav" id="mobileNav"></div>

<!-- Layout -->
<div class="layout">
    <!-- Sidebar -->
    <nav class="sidebar" id="sidebar"></nav>

    <!-- Main -->
    <main class="main-content" id="mainContent">
        <div class="start-screen" id="startScreen">
            <h2>🚂 铁路就业刷题</h2>
            <p>选择左侧题型分类，开始你的刷题之旅</p>
            <div class="start-options">
                <button onclick="startPractice('行测')">
                    📊 行测练习（言语·数量·判断·常识）
                </button>
                <button onclick="startPractice('专业')">
                    🔧 专业笔试（机车·信号·供电·工务·运输）
                </button>
                <button onclick="startPractice('情景模拟')">
                    🎯 情景模拟（处理实际问题）
                </button>
                <button onclick="startPractice('性格测试')">
                    💡 性格测试（了解企业偏好）
                </button>
                <button onclick="startPractice('all')">
                    🔄 综合随机练习（混合出题）
                </button>
                <button onclick="startDaily()">
                    📅 每日一练（行测+专业混搭）
                </button>
            </div>
        </div>
        <div id="questionArea" style="display:none;"></div>
    </main>
</div>

<!-- Answer Sheet Toggle -->
<button class="answer-sheet-toggle" id="sheetToggle" onclick="toggleSheet()">📋</button>

<!-- Answer Sheet Overlay -->
<div class="answer-sheet-overlay" id="sheetOverlay" onclick="toggleSheet()"></div>

<!-- Answer Sheet -->
<div class="answer-sheet" id="answerSheet">
    <button class="close-btn" onclick="toggleSheet()">✕</button>
    <h3>📋 答题卡</h3>
    <div class="stats">
        <div class="stat-item"><div class="num" id="totalCount">0</div><div class="label">总题数</div></div>
        <div class="stat-item"><div class="num correct-num" id="correctCount">0</div><div class="label">✓ 正确</div></div>
        <div class="stat-item"><div class="num wrong-num" id="wrongCount">0</div><div class="label">✗ 错误</div></div>
        <div class="stat-item"><div class="num" id="unansweredCount">0</div><div class="label">未答</div></div>
    </div>
    <div class="answer-grid" id="answerGrid"></div>
</div>

<script>
// ===== App State =====
const state = {
    questions: [],
    currentIndex: 0,
    answers: {},        // { questionId: 'A' }
    answeredStatus: {}, // { questionId: 'correct' | 'wrong' }
    confirmed: {},      // { questionId: true } 已提交确认
    timer: 0,
    timerInterval: null,
    category: null,
    subType: null,
    isComplete: false,
};

// ===== API Calls =====
async function api(url) {
    const resp = await fetch(url);
    return resp.json();
}

// ===== Init =====
async function init() {
    const resp = await api('/api/categories');
    const cats = resp.data;

    // Sidebar
    const sidebar = document.getElementById('sidebar');
    let sidebarHTML = '<div class="sidebar-section"><div class="sidebar-title">题型分类</div>';
    sidebarHTML += `<div class="sidebar-item" onclick="startPractice('all')" data-cat="all">
        🔄 综合练习 <span class="count-badge">${Object.values(cats).reduce((a,b) => a+b.count, 0)}</span>
    </div>`;
    for (const [cat, info] of Object.entries(cats)) {
        const emoji = cat === '行测' ? '📊' : cat === '专业' ? '🔧' : cat === '情景模拟' ? '🎯' : '💡';
        sidebarHTML += `<div class="sidebar-item" onclick="startPractice('${cat}')" data-cat="${cat}">
            ${emoji} ${cat} <span class="count-badge">${info.count}</span>
        </div>`;
    }
    sidebarHTML += '</div>';
    sidebar.innerHTML = sidebarHTML;

    // Mobile nav
    const mobileNav = document.getElementById('mobileNav');
    let mobileHTML = `<button class="cat-btn" onclick="startPractice('all')">综合</button>`;
    for (const cat of Object.keys(cats)) {
        mobileHTML += `<button class="cat-btn" onclick="startPractice('${cat}')">${cat}</button>`;
    }
    mobileNav.innerHTML = mobileHTML;

    // Update sidebar active
    updateSidebarActive('all');
}

// ===== Daily Practice =====
async function startDaily() {
    const resp = await api('/api/daily');
    state.questions = resp.data.items;
    if (state.questions.length === 0) return;

    state.category = 'all';
    state.currentIndex = 0;
    state.answers = {};
    state.answeredStatus = {};
    state.confirmed = {};
    state.timer = 0;
    state.isComplete = false;

    if (state.timerInterval) clearInterval(state.timerInterval);
    state.timerInterval = setInterval(() => { state.timer++; updateTimer(); }, 1000);

    document.getElementById('startScreen').style.display = 'none';
    document.getElementById('questionArea').style.display = 'block';
    updateSidebarActive('all');
    renderQuestion();
    updateProgress();
    updateAnswerSheet();
}

// ===== Start Practice =====
async function startPractice(category) {
    // Stop timer
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }

    state.category = category;
    state.currentIndex = 0;
    state.answers = {};
    state.answeredStatus = {};
    state.confirmed = {};
    state.timer = 0;
    state.isComplete = false;

    document.getElementById('startScreen').style.display = 'none';
    document.getElementById('questionArea').style.display = 'block';

    updateSidebarActive(category);

    let url;
    if (category === 'all') {
        url = '/api/questions/random?count=15';
    } else {
        url = `/api/questions/random?category=${category}&count=15`;
    }

    const resp = await api(url);
    state.questions = resp.data.items;

    if (state.questions.length === 0) {
        document.getElementById('questionArea').innerHTML = `
            <div class="empty-state">
                <div class="big-icon">📭</div>
                <p>暂无题目，请选择其他分类</p>
            </div>`;
        return;
    }

    // Start timer
    state.timerInterval = setInterval(() => {
        state.timer++;
        updateTimer();
    }, 1000);

    renderQuestion();
    updateProgress();
    updateAnswerSheet();
}

// ===== Render Question =====
function renderQuestion() {
    const q = state.questions[state.currentIndex];
    if (!q) return;

    const total = state.questions.length;
    const current = state.currentIndex + 1;
    const isConfirmed = state.confirmed[q.id];
    const selected = state.answers[q.id];

    let optionsHTML = '';
    const labels = ['A', 'B', 'C', 'D'];
    for (const label of labels) {
        if (!q.options[label]) continue;
        let cls = 'option-item';
        if (selected === label && !isConfirmed) cls += ' selected';
        if (isConfirmed) cls += ' disabled';
        if (isConfirmed) {
            if (label === q.answer) cls += ' correct';
            else if (label === selected) cls += ' wrong';
        }
        if (isConfirmed) {
            optionsHTML += `
                <div class="${cls}">
                    <span class="label">${label}</span>
                    <span class="option-text">${q.options[label]}</span>
                </div>`;
        } else {
            optionsHTML += `
                <div class="${cls}" onclick="selectOption('${label}')">
                    <span class="label">${label}</span>
                    <span class="option-text">${q.options[label]}</span>
                </div>`;
        }
    }

    const result = state.answeredStatus[q.id];
    let analysisHTML = '';
    if (isConfirmed) {
        const isCorrect = result === 'correct';
        analysisHTML = `
            <div class="analysis-box show">
                <div class="result-badge ${isCorrect ? 'result-correct' : 'result-wrong'}">
                    ${isCorrect ? '✅ 回答正确' : '❌ 回答错误'}
                </div>
                <div class="correct-answer">正确答案：${q.answer}</div>
                <div class="result-text">${q.analysis}</div>
            </div>`;
    }

    document.getElementById('questionArea').innerHTML = `
        <div class="question-card">
            <div class="question-header">
                <div class="question-number">第 <span class="num">${current}</span> / ${total} 题</div>
                <span class="question-type-badge">${q.type}</span>
            </div>
            <div class="question-text">${q.question}</div>
            <div class="options-list">${optionsHTML}</div>
            ${analysisHTML}
            <div class="bottom-bar">
                <div class="nav-buttons">
                    <button class="btn btn-outline btn-sm" onclick="prevQuestion()" ${state.currentIndex === 0 ? 'disabled' : ''}>← 上一题</button>
                    <button class="btn btn-outline btn-sm" onclick="nextQuestion()" ${state.currentIndex === total - 1 ? 'disabled' : ''}>下一题 →</button>
                </div>
                <div>
                    ${!isConfirmed ? `<button class="btn btn-primary" id="submitBtn" onclick="submitAnswer()" disabled>提交答案</button>`
                        : `<button class="btn btn-outline btn-sm" onclick="toggleSheet()">📋 答题卡</button>
                           ${state.currentIndex < total - 1 ? '<button class="btn btn-primary btn-sm" onclick="nextQuestion()">下一题 →</button>' : '<button class="btn btn-success btn-sm" onclick="finishPractice()">🎉 完成练习</button>'}`}
                </div>
            </div>
        </div>`;

    // Update submit button state
    updateSubmitBtn();
    updateProgress();
}

// ===== Select Option =====
function selectOption(label) {
    const q = state.questions[state.currentIndex];
    if (state.confirmed[q.id]) return;

    state.answers[q.id] = label;
    renderQuestion();
}

// ===== Submit Answer =====
function submitAnswer() {
    const q = state.questions[state.currentIndex];
    const selected = state.answers[q.id];
    if (!selected || state.confirmed[q.id]) return;

    state.confirmed[q.id] = true;
    state.answeredStatus[q.id] = (selected === q.answer) ? 'correct' : 'wrong';
    renderQuestion();
    updateAnswerSheet();
}

// ===== Navigation =====
function prevQuestion() {
    if (state.currentIndex > 0) {
        state.currentIndex--;
        renderQuestion();
    }
}

function nextQuestion() {
    if (state.currentIndex < state.questions.length - 1) {
        state.currentIndex++;
        renderQuestion();
    }
}

// ===== Finish Practice =====
function finishPractice() {
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }

    const total = state.questions.length;
    const answered = Object.keys(state.answers).length;
    const correct = Object.values(state.answeredStatus).filter(s => s === 'correct').length;
    const wrong = Object.values(state.answeredStatus).filter(s => s === 'wrong').length;
    const accuracy = answered > 0 ? Math.round(correct / answered * 100) : 0;
    const timeStr = formatTime(state.timer);

    document.getElementById('questionArea').innerHTML = `
        <div class="question-card" style="text-align:center;padding:40px;">
            <div style="font-size:48px;margin-bottom:12px;">🎉</div>
            <h2 style="color:#1a73e8;margin-bottom:8px;">练习完成！</h2>
            <div style="display:flex;justify-content:center;gap:32px;margin:24px 0;flex-wrap:wrap;">
                <div style="text-align:center;">
                    <div style="font-size:28px;font-weight:700;color:#333;">${total}</div>
                    <div style="font-size:13px;color:#888;">总题数</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:28px;font-weight:700;color:#34a853;">${correct}</div>
                    <div style="font-size:13px;color:#888;">正确</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:28px;font-weight:700;color:#ea4335;">${wrong}</div>
                    <div style="font-size:13px;color:#888;">错误</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:28px;font-weight:700;color:#1a73e8;">${accuracy}%</div>
                    <div style="font-size:13px;color:#888;">正确率</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:28px;font-weight:700;color:#f9a825;">${timeStr}</div>
                    <div style="font-size:13px;color:#888;">用时</div>
                </div>
            </div>
            <div style="margin-top:20px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
                <button class="btn btn-primary" onclick="startPractice('${state.category}')">🔄 再来一组</button>
                <button class="btn btn-outline" onclick="backToStart()">🏠 返回首页</button>
                <button class="btn btn-outline" onclick="reviewMistakes()" ${wrong === 0 ? 'disabled' : ''}>📖 查看错题</button>
            </div>
        </div>`;
    state.isComplete = true;
}

function reviewMistakes() {
    // Filter wrong questions and start a new practice
    const wrongQuestions = state.questions.filter(q => state.answeredStatus[q.id] === 'wrong');
    if (wrongQuestions.length === 0) return;

    // Replace questions with wrong ones
    state.questions = wrongQuestions;
    state.currentIndex = 0;
    state.answers = {};
    state.answeredStatus = {};
    state.confirmed = {};
    state.timer = 0;
    state.isComplete = false;

    if (state.timerInterval) clearInterval(state.timerInterval);
    state.timerInterval = setInterval(() => {
        state.timer++;
        updateTimer();
    }, 1000);

    document.getElementById('startScreen').style.display = 'none';
    document.getElementById('questionArea').style.display = 'block';
    renderQuestion();
    updateProgress();
    updateAnswerSheet();
}

function backToStart() {
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }
    document.getElementById('startScreen').style.display = 'block';
    document.getElementById('questionArea').style.display = 'none';
    updateSidebarActive('all');
}

// ===== Answer Sheet =====
function toggleSheet() {
    const overlay = document.getElementById('sheetOverlay');
    const sheet = document.getElementById('answerSheet');
    overlay.classList.toggle('show');
    sheet.classList.toggle('show');
    updateAnswerSheet();
}

function updateAnswerSheet() {
    const total = state.questions.length;
    const answered = Object.keys(state.answers).length;
    const correct = Object.values(state.answeredStatus).filter(s => s === 'correct').length;
    const wrong = Object.values(state.answeredStatus).filter(s => s === 'wrong').length;

    document.getElementById('totalCount').textContent = total;
    document.getElementById('correctCount').textContent = correct;
    document.getElementById('wrongCount').textContent = wrong;
    document.getElementById('unansweredCount').textContent = total - answered;

    let gridHTML = '';
    state.questions.forEach((q, i) => {
        let cls = 'grid-item';
        if (i === state.currentIndex) cls += ' current';
        if (state.answeredStatus[q.id] === 'correct') cls += ' answered';
        else if (state.answeredStatus[q.id] === 'wrong') cls += ' answered-wrong';
        else if (state.answers[q.id]) cls += ' answered';

        gridHTML += `<div class="${cls}" onclick="jumpToQuestion(${i})">${i + 1}</div>`;
    });
    document.getElementById('answerGrid').innerHTML = gridHTML;
}

function jumpToQuestion(index) {
    state.currentIndex = index;
    renderQuestion();
    toggleSheet();
}

// ===== Utils =====
function updateSubmitBtn() {
    const q = state.questions[state.currentIndex];
    if (!q) return;
    const btn = document.getElementById('submitBtn');
    if (btn) {
        btn.disabled = !state.answers[q.id] || state.confirmed[q.id];
    }
}

function updateProgress() {
    const total = state.questions.length;
    const answered = Object.keys(state.answers).length;
    document.getElementById('progressText').textContent = `${answered}/${total}`;
}

function updateTimer() {
    document.getElementById('timer').textContent = formatTime(state.timer);
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function updateSidebarActive(cat) {
    document.querySelectorAll('.sidebar-item').forEach(el => {
        el.classList.toggle('active', el.dataset.cat === cat);
    });
    document.querySelectorAll('.mobile-category-nav .cat-btn').forEach(el => {
        el.classList.toggle('active', el.textContent.trim() === cat || (cat === 'all' && el.textContent.trim() === '综合'));
    });
}

// ===== Keyboard shortcuts =====
document.addEventListener('keydown', (e) => {
    if (state.isComplete || state.questions.length === 0) return;
    const q = state.questions[state.currentIndex];
    if (!q) return;

    if (e.key === '1' || e.key === 'a' || e.key === 'A') selectOption('A');
    else if (e.key === '2' || e.key === 'b' || e.key === 'B') selectOption('B');
    else if (e.key === '3' || e.key === 'c' || e.key === 'C') selectOption('C');
    else if (e.key === '4' || e.key === 'd' || e.key === 'D') selectOption('D');
    else if (e.key === 'Enter') submitAnswer();
    else if (e.key === 'ArrowLeft') prevQuestion();
    else if (e.key === 'ArrowRight') nextQuestion();
});

// ===== Start =====
init();
</script>
</body>
</html>
"""


@app.get("/exam", response_class=HTMLResponse)
def exam_page():
    return EXAM_HTML


@app.get("/", response_class=HTMLResponse)
def root():
    return EXAM_HTML