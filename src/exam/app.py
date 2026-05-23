"""铁路就业题库 Web 应用 - 完整重写（模拟考试 + 分层训练 + 错题集）"""

import json
import random
import logging
from typing import Any
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from exam.questions import QUESTIONS

logger = logging.getLogger(__name__)

app = FastAPI(title="广铁机考模拟题库")

import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ============================================================
# 模拟考试试卷生成
# 固定配置：45题，单选37(2分)+多选4(4分)+填空4(2.5分)，满分100分
# ============================================================
EXAM_CONFIG = {
    "单选": [
        ("图形推理", 13),
        ("数字推理", 12),
        ("言语理解", 5),
        ("高中数学", 4),
        ("高中物理", 3),
    ],
    "多选": 4,
    "填空": 4,
    "duration": 45,  # 分钟
}

@app.get("/api/exam/generate")
def generate_exam():
    """生成一套模拟考试试卷"""
    selected = []
    qid_offset = 0

    # 1. 单选
    for qtype, count in EXAM_CONFIG["单选"]:
        pool = [q for q in QUESTIONS if q["type"] == qtype and q["question_type"] == "单选"]
        chosen = random.sample(pool, min(count, len(pool)))
        for q in chosen:
            item = dict(q)
            item["exam_index"] = qid_offset + 1
            # 前端判题用，不返回答案
            if "answer" in item:
                del item["answer"]
            if "analysis" in item:
                del item["analysis"]
            selected.append(item)
            qid_offset += 1

    # 2. 多选
    multi_pool = [q for q in QUESTIONS if q["question_type"] == "多选"]
    chosen = random.sample(multi_pool, min(EXAM_CONFIG["多选"], len(multi_pool)))
    for q in chosen:
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item:
            del item["answer"]
        if "analysis" in item:
            del item["analysis"]
        selected.append(item)
        qid_offset += 1

    # 3. 填空
    fill_pool = [q for q in QUESTIONS if q["question_type"] == "填空"]
    chosen = random.sample(fill_pool, min(EXAM_CONFIG["填空"], len(fill_pool)))
    for q in chosen:
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item:
            del item["answer"]
        if "analysis" in item:
            del item["analysis"]
        selected.append(item)
        qid_offset += 1

    # 打乱顺序
    random.shuffle(selected)

    return {
        "code": 0,
        "data": {
            "items": selected,
            "duration": EXAM_CONFIG["duration"],
        }
    }


@app.get("/api/exam/generate_gt")
def generate_gt_exam():
    """生成广铁限时模拟题（按顺序：37单选→4多选→4填空）"""
    selected = []
    qid_offset = 0

    # 1. 单选（按题型顺序出题）
    for qtype, count in EXAM_CONFIG["单选"]:
        pool = [q for q in QUESTIONS if q["type"] == qtype and q["question_type"] == "单选"]
        chosen = random.sample(pool, min(count, len(pool)))
        for q in chosen:
            item = dict(q)
            item["exam_index"] = qid_offset + 1
            if "answer" in item:
                del item["answer"]
            if "analysis" in item:
                del item["analysis"]
            selected.append(item)
            qid_offset += 1

    # 2. 多选
    multi_pool = [q for q in QUESTIONS if q["question_type"] == "多选"]
    chosen = random.sample(multi_pool, min(EXAM_CONFIG["多选"], len(multi_pool)))
    for q in chosen:
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item:
            del item["answer"]
        if "analysis" in item:
            del item["analysis"]
        selected.append(item)
        qid_offset += 1

    # 3. 填空
    fill_pool = [q for q in QUESTIONS if q["question_type"] == "填空"]
    chosen = random.sample(fill_pool, min(EXAM_CONFIG["填空"], len(fill_pool)))
    for q in chosen:
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item:
            del item["answer"]
        if "analysis" in item:
            del item["analysis"]
        selected.append(item)
        qid_offset += 1

    # 不shuffle，保持顺序：单选→多选→填空
    return {
        "code": 0,
        "data": {
            "items": selected,
            "duration": EXAM_CONFIG["duration"],
            "title": "广铁限时模拟题",
        }
    }


class ExamSubmitRequest(BaseModel):
    answers: list[dict[str, Any]]  # [{"exam_index": 1, "selected": "A"}, ...]
    time_used: int  # 秒


@app.post("/api/exam/submit")
def submit_exam(req: ExamSubmitRequest):
    """提交模拟考试并计分"""
    answer_map = {}
    for q in QUESTIONS:
        answer_map[q["id"]] = q

    # 从req.answers重建试卷，这里不能用exam_index找答案
    # 因为exam_index只在试卷中有效
    # 直接用id匹配
    total_score = 0.0
    details = []
    for ans in req.answers:
        qid = ans.get("id")
        q = answer_map.get(qid)
        if not q:
            continue
        selected = ans.get("selected", "")
        correct = False

        if q["question_type"] == "填空":
            # 填空题：忽略空格和大小写
            correct = str(selected).strip().lower() == str(q["answer"]).strip().lower()
        elif q["question_type"] == "多选":
            # 多选题：需要完全匹配（顺序无关）
            user_ans = set(str(selected).split(",")) if isinstance(selected, str) else set()
            correct_ans = set(q["answer"]) if isinstance(q["answer"], list) else set()
            correct_ans_str = {str(a).strip() for a in correct_ans}
            correct = user_ans == correct_ans_str
        else:
            correct = str(selected).strip().upper() == str(q["answer"]).strip().upper()

        if correct:
            total_score += q.get("score", 2.0)

        details.append({
            "id": qid,
            "correct": correct,
            "answer": q["answer"],
            "analysis": q["analysis"],
            "score": q.get("score", 2.0),
            "user_answer": selected,
        })

    return {
        "code": 0,
        "data": {
            "total_score": round(total_score, 1),
            "full_score": 100.0,
            "details": details,
            "time_used": req.time_used,
        }
    }


# ============================================================
# 分层训练
# ============================================================
@app.get("/api/train/types")
def get_train_types():
    """获取所有可训练的类型 (不返回题目数量)，图形推理排在首位"""
    seen = set()
    for q in QUESTIONS:
        if q["question_type"] in ("单选", "多选"):
            seen.add(q["type"])
    # 固定顺序：图形推理排首位，其余按科目逻辑排序
    type_order = ["图形推理", "数字推理", "言语理解", "文学常识", "地理常识", "数学物理", "高中数学", "高中物理", "综合"]
    type_order = [t for t in type_order if t in seen]
    return {"code": 0, "data": type_order}


@app.get("/api/train/questions")
def get_train_questions(
    type_name: str = Query(alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(1, ge=1, le=5),
):
    """获取分层训练题目（不返回总数量）"""
    filtered = [q for q in QUESTIONS if q["type"] == type_name and q["question_type"] in ("单选", "多选")]
    if not filtered:
        return {"code": 0, "data": {"items": [], "has_more": False}}

    # 排序后切片（不shuffle，保证分页不重复）
    filtered.sort(key=lambda x: x["id"])

    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    has_more = end < len(filtered)

    # 不返回答案（前端判题用）
    result_items = []
    for item in items:
        citem = dict(item)
        if "answer" in citem:
            del citem["answer"]
        if "analysis" in citem:
            del citem["analysis"]
        result_items.append(citem)

    return {
        "code": 0,
        "data": {
            "items": result_items,
            "has_more": has_more,
        }
    }


class TrainSubmitRequest(BaseModel):
    question_id: int
    selected: str


@app.post("/api/train/submit")
def submit_train(req: TrainSubmitRequest):
    """提交分层训练单题答案"""
    for q in QUESTIONS:
        if q["id"] == req.question_id:
            correct = False
            selected = req.selected.strip()

            if q["question_type"] == "多选":
                user_ans = set(selected.split(",")) if selected else set()
                correct_ans = set(q["answer"]) if isinstance(q["answer"], list) else set()
                correct = user_ans == correct_ans
            else:
                correct = selected.upper() == str(q["answer"]).strip().upper()

            return {
                "code": 0,
                "data": {
                    "correct": correct,
                    "answer": q["answer"],
                    "analysis": q["analysis"],
                }
            }

    raise HTTPException(status_code=404, detail="题目不存在")


# ============================================================
# 错题集
# ============================================================
class WrongListRequest(BaseModel):
    ids: list[int]


@app.post("/api/wrong/list")
def get_wrong_questions(req: WrongListRequest):
    """根据ID列表获取错题详情"""
    qmap = {q["id"]: q for q in QUESTIONS}
    items = []
    for qid in req.ids:
        if qid in qmap:
            items.append(qmap[qid])
    return {"code": 0, "data": {"items": items}}


# ============================================================
# 前端页面
# ============================================================
EXAM_HTML = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>广铁机考模拟题库</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:#f0f2f5;color:#333;min-height:100vh}
/* 首页 */
.home-page{max-width:800px;margin:0 auto;padding:60px 24px 40px}
.home-title{font-size:28px;font-weight:700;color:#1a73e8;text-align:center;margin-bottom:8px}
.home-sub{text-align:center;color:#888;font-size:15px;margin-bottom:40px}
.home-cards{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.home-card{background:#fff;border-radius:16px;padding:32px;cursor:pointer;box-shadow:0 2px 12px rgba(0,0,0,0.08);transition:all 0.3s;text-align:center}
.home-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,0.12)}
.home-card .icon{font-size:48px;margin-bottom:16px}
.home-card .name{font-size:20px;font-weight:600;color:#333;margin-bottom:8px}
.home-card .desc{font-size:14px;color:#999;line-height:1.6}
.home-card.exam{border-top:4px solid #ff6b35}
.home-card.train{border-top:4px solid #1a73e8}
.home-footer{text-align:center;margin-top:40px;font-size:13px;color:#bbb}
.home-footer .btn{display:inline-block;padding:8px 20px;border:1px solid #ddd;border-radius:20px;color:#999;font-size:13px;cursor:pointer;background:#fff;margin:0 6px}
.home-footer .btn:hover{background:#f5f5f5}
.blessing{text-align:center;margin:12px 0 8px;padding:8px 12px;font-size:15px;color:#ff6b35;font-weight:500;background:linear-gradient(135deg,#fff5f0,#fff0e6);border-radius:12px;border:1px solid #ffe0cc}
/* Header */
.header{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;padding:0 20px;height:52px;display:flex;align-items:center;position:fixed;top:0;left:0;right:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,0.15)}
.header .back{background:none;border:none;color:#fff;font-size:22px;cursor:pointer;padding:4px 8px;margin-right:8px;display:flex;align-items:center}
.header .title{font-size:17px;font-weight:600;flex:1}
.header .right{font-size:14px;display:flex;align-items:center;gap:12px}
.timer-badge{background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:12px;font-variant-numeric:tabular-nums;font-size:14px}
/* Layout */
.page{display:none;padding-top:52px;min-height:100vh}
.page.active{display:block}
/* Main Content Area */
.content{padding:16px;max-width:800px;margin:0 auto}
/* Type Selector */
.type-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0 24px}
.type-btn{background:#fff;border:2px solid #e8e8e8;border-radius:12px;padding:20px 16px;text-align:center;cursor:pointer;transition:all 0.3s;font-size:15px;font-weight:500}
.type-btn:hover{border-color:#1a73e8;color:#1a73e8}
.type-btn:active{transform:scale(0.97)}
/* Question Card */
.q-card{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.08);padding:20px;margin-bottom:16px}
.q-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:6px}
.q-num{font-size:13px;color:#888}
.q-num .n{color:#1a73e8;font-weight:700}
.q-type{font-size:11px;padding:2px 10px;border-radius:10px;background:#e8f0fe;color:#1a73e8}
.q-text{font-size:15px;line-height:1.8;margin-bottom:16px;white-space:pre-wrap}
.q-img-wrap{margin:8px 0;text-align:center}.q-img-wrap img{max-width:100%;max-height:280px;border-radius:6px;border:1px solid #e0e0e0;background:#f8f8f8}
    .q-img-full{margin:8px 0;text-align:center}.q-img-full img{max-width:100%;width:100%;border-radius:6px;border:1px solid #e0e0e0;background:#f8f8f8}
/* Options */
.options{display:flex;flex-direction:column;gap:8px}
.option{display:flex;align-items:flex-start;gap:10px;padding:12px 14px;border:2px solid #e8e8e8;border-radius:10px;cursor:pointer;transition:all 0.2s;font-size:14px;line-height:1.6}
.option:hover{border-color:#90caf9;background:#f5f9ff}
.option.selected{border-color:#1a73e8;background:#e8f0fe}
.option.correct{border-color:#4caf50;background:#e8f5e9}
.option.wrong{border-color:#f44336;background:#ffebee}
.option .letter{width:24px;height:24px;border-radius:50%;background:#f0f0f0;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;flex-shrink:0}
.option.selected .letter{background:#1a73e8;color:#fff}
.option.correct .letter{background:#4caf50;color:#fff}
.option.wrong .letter{background:#f44336;color:#fff}
/* 填空题输入 */
.fill-input{width:100%;padding:12px 16px;border:2px solid #e0e0e0;border-radius:10px;font-size:16px;outline:none;transition:border-color 0.2s}
.fill-input:focus{border-color:#1a73e8}
.fill-input.correct{border-color:#4caf50;background:#f1faf1}
.fill-input.wrong{border-color:#f44336;background:#fff5f5}
/* Analysis */
.analysis-box{background:#fffbe6;border:1px solid #ffe58f;border-radius:10px;padding:14px;margin-top:14px;font-size:14px;color:#8c6e00;line-height:1.7}
.analysis-box .label{font-weight:600;color:#d48806}
.analysis-box.correct{background:#f1faf1;border-color:#b7eb8f;color:#2e7d32}
.analysis-box.correct .label{color:#2e7d32}
/* Buttons */
.btn{display:inline-block;padding:12px 28px;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;transition:all 0.2s;text-align:center}
.btn:active{transform:scale(0.97)}
.btn-primary{background:#1a73e8;color:#fff}
.btn-primary:hover{background:#1557b0}
.btn-primary:disabled{background:#a0c4ff;cursor:not-allowed}
.btn-success{background:#4caf50;color:#fff}
.btn-success:hover{background:#388e3c}
.btn-warning{background:#ff6b35;color:#fff}
.btn-warning:hover{background:#e55a2b}
.btn-outline{background:#fff;color:#666;border:1px solid #ddd}
.btn-outline:hover{background:#f5f5f5}
.btn-block{display:block;width:100%}
.btn-sm{padding:8px 16px;font-size:13px}
/* Exam footer */
.exam-footer{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
/* Exam Q-nav sidebar */
.exam-wrap{display:flex;gap:16px;max-width:900px;margin:0 auto;position:relative}
.exam-main{flex:1;min-width:0}
/* Result */
.result-card{background:#fff;border-radius:16px;padding:32px;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-bottom:20px}
.result-score{font-size:64px;font-weight:700;color:#1a73e8;margin:16px 0}
.result-score .unit{font-size:24px;color:#999}
.result-info{font-size:14px;color:#888;margin-bottom:20px;line-height:1.8}
.result-detail-item{padding:10px;margin:4px 0;border-radius:8px;font-size:13px;display:flex;justify-content:space-between;align-items:center}
.result-detail-item.correct{background:#e8f5e9;color:#2e7d32}
.result-detail-item.wrong{background:#ffebee;color:#c62828}
/* Wrong book */
.wrong-item{background:#fff;border-radius:12px;padding:20px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,0.06)}
.wrong-empty{text-align:center;padding:60px 20px;color:#999}
.wrong-empty .icon{font-size:48px;margin-bottom:16px}
/* 多选标签 */
.multi-hint{font-size:12px;color:#ff6b35;margin-bottom:8px;font-weight:500}
/* Scrollbar */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-thumb{background:#ccc;border-radius:3px}
.submit-top-btn{display:inline-block;padding:6px 14px;background:#e74c3c;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;margin-left:8px;transition:background .2s}
.submit-top-btn:hover{background:#c0392b}
/* Mobile */
@media(max-width:640px){
.home-cards{grid-template-columns:1fr}
.home-page{padding:40px 16px 20px}
.home-title{font-size:24px}
.type-grid{grid-template-columns:1fr 1fr}
.content{padding:12px}
.q-card{padding:16px}
.result-score{font-size:48px}
}
</style>
</head>
<body>

<!-- ========== 首页 ========== -->
<div id="pageHome" class="page active">
  <div class="home-page">
    <div class="home-title">广铁机考模拟题库</div>
    <div class="home-sub">广州铁路局机考模拟 · 分层训练</div>
    <div class="blessing">🌟 祝你考试顺利，成功上岸！</div>
    <div class="home-cards">
      <div class="home-card" style="border-top:4px solid #e91e63" onclick="startGTExam()">
        <div class="icon">🎯</div>
        <div class="name">广铁限时模拟题</div>
        <div class="desc">45分钟限时答题<br>37单选 → 4多选 → 4填空<br>按序出题，自动算分</div>
      </div>
      <div class="home-card train" onclick="startTrain()">
        <div class="icon">📚</div>
        <div class="name">分层训练</div>
        <div class="desc">按题型分类练习<br>图形推理·数字推理·言语理解<br>文学常识·地理常识·数学物理</div>
      </div>
    </div>
    <div class="home-footer">
      <span class="btn" onclick="showWrongBook()">📕 错题本</span>
    </div>
  </div>
</div>

<!-- ========== 模拟考试页 ========== -->
<div id="pageExam" class="page">
  <div class="header">
    <button class="back" onclick="backHome()">&#x2190;</button>
    <span class="title">广铁限时模拟题</span>
    <div class="right">
      <span class="timer-badge" id="examTimer">45:00</span>
      <button class="submit-top-btn" onclick="submitExam()">提交试卷</button>
    </div>
  </div>
  <div class="content">
    <div class="exam-wrap">
      <div class="exam-main" id="examContent">
        <div style="text-align:center;padding:60px 0;color:#999">加载中...</div>
      </div>

    </div>
  </div>
</div>

<!-- ========== 成绩页 ========== -->
<div id="pageResult" class="page">
  <div class="header">
    <button class="back" onclick="backHome()">&#x2190;</button>
    <span class="title">考试成绩</span>
    <div class="right"></div>
  </div>
  <div class="content" id="resultContent">
  </div>
</div>

<!-- ========== 分层训练页 ========== -->
<div id="pageTrain" class="page">
  <div class="header">
    <button class="back" onclick="backHome()">&#x2190;</button>
    <span class="title">分层训练</span>
    <div class="right"></div>
  </div>
  <div class="content" id="trainContent">
  </div>
</div>

<!-- ========== 错题本页 ========== -->
<div id="pageWrong" class="page">
  <div class="header">
    <button class="back" onclick="backHome()">&#x2190;</button>
    <span class="title">错题本</span>
    <div class="right"></div>
  </div>
  <div class="content" id="wrongContent">
  </div>
</div>

<script>
// ========== 页面切换 ==========
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function backHome() {
  if (window.examTimerId) { clearInterval(window.examTimerId); window.examTimerId = null; }
  showPage('pageHome');
}

// ========== 首页按钮 ==========
function startGTExam() { showPage('pageExam'); loadExam(); }
function startTrain() { showPage('pageTrain'); loadTypes(); }
function showWrongBook() { showPage('pageWrong'); loadWrongBook(); }

// ========== 错题本 ==========
function getWrongIds() {
  try { return JSON.parse(localStorage.getItem('wrong_ids') || '[]'); } catch(e) { return []; }
}
function addWrongId(id) {
  let ids = getWrongIds();
  if (!ids.includes(id)) { ids.push(id); localStorage.setItem('wrong_ids', JSON.stringify(ids)); }
}
function removeWrongId(id) {
  let ids = getWrongIds().filter(i => i !== id);
  localStorage.setItem('wrong_ids', JSON.stringify(ids));
}

function loadWrongBook() {
  const el = document.getElementById('wrongContent');
  const ids = getWrongIds();
  if (ids.length === 0) {
    el.innerHTML = '<div class="wrong-empty"><div class="icon">🎉</div><p>暂无错题记录</p><p style="font-size:13px;margin-top:8px">继续加油练习吧！</p></div>';
    return;
  }
  el.innerHTML = '<div style="text-align:center;padding:20px;color:#999">加载中...</div>';
  fetch('./api/wrong/list', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})})
    .then(r=>r.json()).then(res=>{
      if(res.code!==0||!res.data.items.length){el.innerHTML='<div class="wrong-empty"><p>暂无错题</p></div>';return}
      let html = '<div style="margin:16px 0;text-align:right"><button class="btn btn-sm btn-outline" onclick="clearWrongBook()">清空错题本</button></div>';
      res.data.items.forEach(q=>{
        html += '<div class="wrong-item">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">';
        html += '<span style="font-size:12px;color:#888">'+q.type+' · '+q.question_type+'</span>';
        html += '<span style="font-size:12px;color:#f44336;cursor:pointer" onclick="removeWrongId('+q.id+');loadWrongBook()">✕ 移除</span>';
        html += '</div>';
        if(q.image && q.type==='图形推理'){
        html += '<div class="q-img-full"><img src="static/'+q.image[0]+'" alt="题图"></div>';
      } else {
        html += '<div style="font-size:14px;line-height:1.8;white-space:pre-wrap;margin-bottom:10px">'+htmlEscape(q.question)+'</div>';
      }
      if(q.image && q.type!=='图形推理'){
        html += '<div class="q-img-wrap"><img src="static/'+q.image[0]+'" alt="题图"></div>';
      }
        if(q.options){
          html += '<div style="font-size:13px;color:#666;margin-bottom:6px">选项：</div>';
          Object.entries(q.options).forEach(([k,v])=>{
            html += '<div style="font-size:13px;padding:4px 0">'+k+'. '+htmlEscape(v)+'</div>';
          });
        }
        html += '<div style="margin-top:10px;padding:10px;background:#fffbe6;border-radius:8px;font-size:13px">';
        html += '<span style="color:#d48806;font-weight:600">正确答案：</span> ';
        html += Array.isArray(q.answer) ? q.answer.join(', ') : q.answer;
        if(q.analysis) html += '<br><span style="color:#d48806;font-weight:600">解析：</span>'+htmlEscape(q.analysis);
        html += '</div></div>';
      });
      el.innerHTML = html;
    }).catch(()=>{el.innerHTML='<div class="wrong-empty"><p>加载失败</p></div>'});
}

function clearWrongBook() {
  if(confirm('确定清空所有错题记录？')){localStorage.setItem('wrong_ids','[]');loadWrongBook()}
}

// ========== 模拟考试 ==========
var examData = null;
var examAnswers = {};
var examTimerId = null;
var examTimeLeft = 0;

function loadExam() {
  const el = document.getElementById('examContent');
  document.querySelector('#pageExam .header .title').textContent = '广铁限时模拟题';
  el.innerHTML = '<div style="text-align:center;padding:60px 0;color:#999">生成试卷中...</div>';
  fetch('./api/exam/generate_gt').then(r=>r.json()).then(res=>{
    if(res.code!==0){el.innerHTML='<div style="text-align:center;padding:60px 0;color:#f44336">生成失败</div>';return}
    examData = res.data;
    examAnswers = {};
    examTimeLeft = res.data.duration * 60;
    renderExam();
    startExamTimer();
  }).catch(()=>{el.innerHTML='<div style="text-align:center;padding:60px 0;color:#f44336">加载失败</div>'});
}

function renderExam() {
  const el = document.getElementById('examContent');
  let html = '<div style="font-size:13px;color:#ff6b35;padding:8px 0;text-align:center">注意：考试限时45分钟，请合理安排时间</div>';
  examData.items.forEach((q,i)=>{
    html += '<div class="q-card" id="eq_'+i+'">';
    html += '<div class="q-header">';
    html += '<span class="q-num">第 <span class="n">'+(i+1)+'</span> 题</span>';
    html += '<span class="q-type">'+q.type+' · '+(q.question_type==='单选'?'单选题':q.question_type==='多选'?'多选题':'填空题')+'</span>';
    html += '</div>';
    if(q.image && q.type==='图形推理'){
      html += '<div class="q-img-full"><img src="static/'+q.image[0]+'" alt="题图"></div>';
    } else {
      html += '<div class="q-text">'+htmlEscape(q.question)+'</div>';
    }
    if(q.image && q.type!=='图形推理'){
      html += '<div class="q-img-wrap"><img src="static/'+q.image[0]+'" alt="题图"></div>';
    }
    if(q.question_type==='填空'){
      html += '<input class="fill-input" id="exam_inp_'+i+'" placeholder="请输入答案" onchange="examAnswers['+q.id+']={id:'+q.id+',selected:this.value}">';
    } else {
      if(q.question_type==='多选') html += '<div class="multi-hint">多选（可点击多个选项）</div>';
      html += '<div class="options" id="exam_opts_'+i+'">';
      Object.entries(q.options||{}).forEach(([k,v])=>{
        html += '<div class="option" onclick="examSelectOpt('+i+','+q.id+',\''+k+'\','+(q.question_type==='多选'?'true':'false')+')">';
        html += '<span class="letter">'+k+'</span>';
        html += '<span>'+htmlEscape(v)+'</span></div>';
      });
      html += '</div>';
    }
    html += '</div>';
  });
  html += '<div class="exam-footer">';
  html += '<button class="btn btn-primary btn-block" onclick="submitExam()" id="examSubmitBtn">提交试卷</button>';
  html += '</div>';
  el.innerHTML = html;
}

// 选答案
window.examSelectOpt = function(i, qid, opt, isMulti) {
  const items = document.getElementById('examContent');
  if(!items) return;
  const cards = items.querySelectorAll('.q-card');
  if(!cards[i]) return;
  const opts = cards[i].querySelector('.options-wrap');
  if(!opts) return;
  
  currentExamQuestion = i;
  
  if(isMulti){
    const el = Array.from(opts.children).find(o=>{
      const letter = o.querySelector('.letter');
      return letter && letter.textContent.trim()===opt;
    });
    if(el) el.classList.toggle('selected');
    const selected = [];
    opts.querySelectorAll('.option.selected').forEach(o=>{
      const letter = o.querySelector('.letter');
      if(letter) selected.push(letter.textContent.trim());
    });
    examAnswers[qid] = {id:qid, selected: selected.join(',')};
  } else {
    opts.querySelectorAll('.option').forEach(o=>o.classList.remove('selected'));
    const el = Array.from(opts.children).find(o=>{
      const letter = o.querySelector('.letter');
      return letter && letter.textContent.trim()===opt;
    });
    if(el) el.classList.add('selected');
    examAnswers[qid] = {id:qid, selected: opt};
  }
}

function startExamTimer() {
  if(examTimerId) clearInterval(examTimerId);
  examTimerId = setInterval(()=>{
    examTimeLeft--;
    if(examTimeLeft<=0){
      clearInterval(examTimerId);
      examTimerId = null;
      document.getElementById('examTimer').textContent = '00:00';
      submitExam();
      return;
    }
    const m = Math.floor(examTimeLeft/60);
    const s = examTimeLeft%60;
    document.getElementById('examTimer').textContent = m.toString().padStart(2,'0')+':'+s.toString().padStart(2,'0');
  },1000);
}

function submitExam() {
  clearInterval(examTimerId);
  examTimerId = null;
  const btn = document.getElementById('examSubmitBtn');
  if(btn) btn.disabled = true;
  // 构建完整45题答案，未答的传空字符串
  const answers = [];
  if(examData && examData.items){
    examData.items.forEach(q=>{
      const ans = examAnswers[q.id];
      answers.push({id: q.id, selected: ans ? ans.selected : ''});
    });
  }
  const timeUsed = examData.duration * 60 - examTimeLeft;
  fetch('./api/exam/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answers,time_used:timeUsed})})
    .then(r=>r.json()).then(res=>{
      if(res.code!==0) return;
      showExamResult(res.data);
    }).catch(e=>{console.error(e)});
}

function showExamResult(data) {
  const el = document.getElementById('resultContent');
  if(!el){alert('页面加载异常，请刷新重试');return;}
  
  // 存储结果数据供筛选使用
  window._examResultData = data;
  window._examFilter = 'all';
  
  // 得分卡片
  let html = '<div class="result-card">';
  html += '<div style="font-size:36px;font-weight:700;color:#e74c3c">'+data.total_score+'</div>';
  html += '<div style="font-size:14px;color:#999">满分 '+data.full_score+' 分</div>';
  html += '<div class="time-used">用时 <b>'+Math.floor(data.time_used/60)+'分'+data.time_used%60+'秒</b></div>';
  let correctCount = data.details.filter(d=>d.correct).length;
  let wrongCount = data.details.length - correctCount;
  let unansweredCount = data.details.filter(d=> !d.user_answer || d.user_answer==='').length;
  html += '<div style="font-size:14px;color:#666;margin-bottom:8px">共 '+data.details.length+' 题 · 正确 '+correctCount+' 题 · 错误 '+wrongCount+' 题'+(unansweredCount>0?' · 未答 '+unansweredCount+' 题':'')+'</div>';
  html += '</div>';
  
  // 按钮组
  html += '<div style="display:flex;gap:10px;margin-bottom:12px">';
  html += '<button onclick="backHome();setTimeout(startGTExam,100)" style="flex:1;padding:10px;background:#3498db;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer">再来一套</button>';
  html += '</div>';
  
  // 查看模式切换
  html += '<div style="display:flex;gap:8px;margin-bottom:12px;padding:10px 0;border-bottom:2px solid #eee">';
  html += '<button id="filterBtnAll" class="filter-btn active" onclick="switchExamFilter(\'all\')" style="flex:1;padding:8px;border-radius:6px;font-size:14px;cursor:pointer;border:none;background:#4a90d9;color:#fff;font-weight:600">📋 全部45题</button>';
  html += '<button id="filterBtnWrong" class="filter-btn" onclick="switchExamFilter(\'wrong\')" style="flex:1;padding:8px;border-radius:6px;font-size:14px;cursor:pointer;border:none;background:#f0f0f0;color:#666">❌ 仅错题 ('+wrongCount+'题)</button>';
  html += '</div>';
  
  // 题目列表容器
  html += '<div id="reviewSection">';
  html += renderExamItems(data.details, 'all');
  html += '</div>';
  
  el.innerHTML = html;
  showPage('pageResult');
  setTimeout(()=>{
    const card = document.querySelector('.result-card');
    if(card) card.scrollIntoView({behavior:'smooth',block:'center'});
  },100);
}

// 渲染题目列表
function renderExamItems(details, filter){
  let html = '';
  details.forEach((d,i)=>{
    if(filter==='wrong' && d.correct) return;
    const q = examData.items[i];
    if(!q) return;
    const isCorrect = d.correct;
    const userAns = d.user_answer || '未作答';
    const correctAns = typeof d.answer==='object' ? (d.answer||[]).join(',') : (d.answer||'');
    const analysisText = d.analysis || '暂无解析';
    
    html += '<div class="result-item '+(isCorrect?'correct-bg':'wrong-bg')+'">';
    html += '<div style="font-size:14px;font-weight:600;color:#333;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #eee">第 '+(i+1)+' 题 <span style="float:right;font-size:13px">'+(isCorrect?'✅ 正确 (+'+d.score+'分)':'❌ 错误')+'</span></div>';
    html += '<div class="q-text">'+htmlEscape(q.question)+'</div>';
    if(q.image && q.type==='图形推理'){
      html += '<div class="q-img-full"><img src="static/'+q.image[0]+'" alt="题图"></div>';
    } else if(q.image){
      html += '<div class="q-img-wrap"><img src="static/'+q.image[0]+'" alt="题图"></div>';
    }
    html += '<div style="margin-top:8px;padding:8px 10px;background:#f8f9fa;border-radius:6px;font-size:14px">';
    html += '<div><span style="font-weight:600">你的答案：</span><span style="color:'+(isCorrect?'#27ae60':'#e74c3c')+';font-weight:600">'+htmlEscape(userAns)+'</span></div>';
    if(!isCorrect){
      html += '<div><span style="font-weight:600">正确答案：</span><span style="color:#27ae60;font-weight:600">'+htmlEscape(correctAns)+'</span></div>';
    }
    html += '</div>';
    // 解析 - 每道题都有
    html += '<div style="margin-top:8px;padding:10px 12px;background:#f0f4ff;border-radius:6px;font-size:13px;color:#444;line-height:1.7;border-left:3px solid #4a90d9">';
    html += '<span style="font-weight:600;color:#4a90d9">📖 解析：</span>'+htmlEscape(analysisText);
    html += '</div>';
    html += '</div>';
    
    if(!isCorrect){
      try{addWrongId(q.id);}catch(e){}
    }
  });
  return html;
}

// 切换查看模式
function switchExamFilter(mode){
  window._examFilter = mode;
  const data = window._examResultData;
  if(!data) return;
  
  const btnAll = document.getElementById('filterBtnAll');
  const btnWrong = document.getElementById('filterBtnWrong');
  if(btnAll){
    btnAll.style.background = mode==='all' ? '#4a90d9' : '#f0f0f0';
    btnAll.style.color = mode==='all' ? '#fff' : '#666';
    btnAll.style.fontWeight = mode==='all' ? '600' : 'normal';
  }
  if(btnWrong){
    btnWrong.style.background = mode==='wrong' ? '#e74c3c' : '#f0f0f0';
    btnWrong.style.color = mode==='wrong' ? '#fff' : '#666';
    btnWrong.style.fontWeight = mode==='wrong' ? '600' : 'normal';
  }
  
  const section = document.getElementById('reviewSection');
  if(section){
    section.innerHTML = renderExamItems(data.details, mode);
  }
}
// ========== 分层训练 ==========
var trainType = '';
var trainPage = 1;

function loadTypes() {
  const el = document.getElementById('trainContent');
  el.innerHTML = '<div style="text-align:center;padding:20px 0;color:#999">加载中...</div>';
  fetch('./api/train/types').then(r=>r.json()).then(res=>{
    if(res.code!==0||!res.data.length){el.innerHTML='<div style="padding:20px;text-align:center;color:#999">暂无题目</div>';return}
    let html = '<div style="padding:12px 0;font-size:14px;color:#666;text-align:center">选择题型开始练习</div><div class="type-grid">';
    res.data.forEach(t=>{
      html += '<div class="type-btn" onclick="startTrainType(\''+t+'\')">'+t+'</div>';
    });
    html += '</div>';
    el.innerHTML = html;
  }).catch(()=>{});
}

function startTrainType(type) {
  trainType = type;
  trainPage = 1;
  showPage('pageTrain');
  loadTrainQuestion();
}

function loadTrainQuestion() {
  const el = document.getElementById('trainContent');
  el.innerHTML = '<div style="text-align:center;padding:40px 0;color:#999">加载中...</div>';
  fetch('./api/train/questions?type='+encodeURIComponent(trainType)+'&page='+trainPage+'&page_size=1')
    .then(r=>r.json()).then(res=>{
      if(res.code!==0||!res.data.items.length){
        el.innerHTML = '<div style="padding:40px;text-align:center"><p style="color:#888;margin-bottom:20px">没有更多题目了</p><button class="btn btn-outline btn-sm" onclick="loadTypes()">返回题型列表</button></div>';
        return;
      }
      renderTrainQuestion(res.data.items[0], res.data.has_more);
    }).catch(()=>{});
}

var currentTrainQ = null;

function renderTrainQuestion(q, hasMore) {
  currentTrainQ = q;
  const el = document.getElementById('trainContent');
  let html = '<div style="display:flex;justify-content:space-between;align-items:center;margin:12px 0">';
  html += '<button class="btn btn-outline btn-sm" onclick="loadTypes()">&larr; 返回题型</button>';
  html += '<span style="font-size:13px;color:#888">'+trainType+'</span>';
  html += '</div>';
  html += '<div class="q-card">';
  html += '<div class="q-header">';
  html += '<span class="q-num">第 <span class="n">'+(trainPage)+'</span> 题</span>';
  html += '<span class="q-type">'+(q.question_type==='多选'?'多选题':'单选题')+'</span>';
  html += '</div>';
  if(q.image && q.type==='图形推理'){
  html += '<div class="q-img-full"><img src="static/'+q.image[0]+'" alt="题图"></div>';
    } else {
  html += '<div class="q-text">'+htmlEscape(q.question)+'</div>';
    }
    if(q.image && q.type!=='图形推理'){
  html += '<div class="q-img-wrap"><img src="static/'+q.image[0]+'" alt="题图"></div>';
    }
  if(q.options){
    if(q.question_type==='多选') html += '<div class="multi-hint">多选（可点击多个选项）</div>';
    html += '<div class="options" id="trainOpts">';
    Object.entries(q.options).forEach(([k,v])=>{
      html += '<div class="option" onclick="trainSelectOpt(\''+k+'\','+(q.question_type==='多选'?'true':'false')+')">';
      html += '<span class="letter">'+k+'</span>';
      html += '<span>'+htmlEscape(v)+'</span></div>';
    });
    html += '</div>';
  }
  html += '<div id="trainResult" style="margin-top:12px"></div>';
  html += '<div style="display:flex;gap:10px;margin-top:14px">';
  html += '<button class="btn btn-primary btn-sm" style="flex:1" id="trainSubmitBtn" onclick="submitTrain()">提交答案</button>';
  if(hasMore) html += '<button class="btn btn-outline btn-sm" onclick="nextTrain()">下一题 &rarr;</button>';
  html += '</div></div>';
  el.innerHTML = html;
  window.trainSelected = q.question_type==='多选'?[]:'';
}

function trainSelectOpt(opt, isMulti) {
  if(isMulti){
    const opts = document.getElementById('trainOpts');
    if(!opts) return;
    opts.querySelectorAll('.option').forEach(o=>{
      o.querySelector('.letter').textContent===opt?o.classList.toggle('selected'):null;
    });
    window.trainSelected = [];
    opts.querySelectorAll('.option.selected').forEach(o=>{
      window.trainSelected.push(o.querySelector('.letter').textContent);
    });
  } else {
    document.querySelectorAll('#trainOpts .option').forEach(o=>o.classList.remove('selected'));
    const opts = document.getElementById('trainOpts');
    if(!opts) return;
    opts.querySelectorAll('.option').forEach(o=>{
      if(o.querySelector('.letter').textContent===opt) o.classList.add('selected');
    });
    window.trainSelected = opt;
  }
}

function submitTrain() {
  if(!currentTrainQ) return;
  const btn = document.getElementById('trainSubmitBtn');
  if(btn) btn.disabled = true;
  const selected = Array.isArray(window.trainSelected)?window.trainSelected.join(','):window.trainSelected;
  if(!selected) { if(btn) btn.disabled = false; return; }
  fetch('./api/train/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_id:currentTrainQ.id,selected})})
    .then(r=>r.json()).then(res=>{
      if(res.code!==0) return;
      showTrainResult(res.data);
      if(!res.data.correct) addWrongId(currentTrainQ.id);
    }).catch(()=>{if(btn) btn.disabled = false});
}

function showTrainResult(data) {
  const opts = document.getElementById('trainOpts');
  const result = document.getElementById('trainResult');
  if(!result) return;
  // 高亮正确答案
  if(opts){
    opts.querySelectorAll('.option').forEach(o=>{
      const letter = o.querySelector('.letter').textContent;
      if(Array.isArray(data.answer)?data.answer.includes(letter):data.answer===letter){
        o.classList.add('correct');
      } else if(o.classList.contains('selected') && !data.correct){
        o.classList.add('wrong');
      }
    });
  }
  result.innerHTML = '<div class="analysis-box '+(data.correct?'correct':'')+'">';
  result.innerHTML += '<span class="label">'+(data.correct?'&#x2713; 回答正确！':'&#x2717; 回答错误')+'</span>';
  result.innerHTML += '<br>正确答案：'+(Array.isArray(data.answer)?data.answer.join(', '):data.answer);
  if(data.analysis) result.innerHTML += '<br><br><span class="label">解析：</span>'+htmlEscape(data.analysis);
  result.innerHTML += '</div>';
}

function nextTrain() {
  trainPage++;
  document.getElementById('trainSubmitBtn').disabled = false;
  loadTrainQuestion();
}

// ========== 工具 ==========
function htmlEscape(s) {
  if(!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>
"""


@app.get("/")
@app.get("/exam")
def exam_page():
    return HTMLResponse(content=EXAM_HTML)


@app.get("/api/health")
def health():
    return {"status": "ok"}