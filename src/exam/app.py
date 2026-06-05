"""铁路就业题库 Web 应用 - 完整重写（模拟考试 + 分层训练 + 错题集）"""

import json
import random
import logging
import time
import hashlib
from typing import Any
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from starlette.responses import Response

from exam.questions import QUESTIONS

logger = logging.getLogger(__name__)

# ============== 性能优化：TTL缓存 ==============
class TTLCache:
    """带过期时间的缓存，用于减少高并发下的重复计算"""
    def __init__(self, ttl=5):
        self._cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key, value):
        self._cache[key] = (value, time.time())

exam_cache = TTLCache(ttl=5)  # 试卷缓存5秒，应对突发并发

# ============== 优化静态文件缓存 ==============
class CacheStaticFiles(StaticFiles):
    """带缓存头的静态文件服务，浏览器缓存图片减少请求"""
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico')):
            response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        elif path.endswith(('.css', '.js')):
            response.headers["Cache-Control"] = "public, max-age=3600"
        return response

app = FastAPI(title="广铁机考模拟题库")
app.add_middleware(GZipMiddleware, minimum_size=500)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", CacheStaticFiles(directory=static_dir), name="static")
app.mount("/exam/static", CacheStaticFiles(directory=static_dir), name="static_exam")

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

# ============== 预计算题目池（启动时一次计算） ==============
_PRE_COMPUTED_POOLS: dict[str, list] = {}
_LAST_POOL_REFRESH: float = 0

def _refresh_pools():
    """预计算所有题型池，避免每次请求重新筛选"""
    global _PRE_COMPUTED_POOLS, _LAST_POOL_REFRESH
    pool = {}
    for qtype, count in EXAM_CONFIG["单选"]:
        pool[qtype] = [q for q in QUESTIONS if q["type"] == qtype and q["question_type"] == "单选"]
    pool["多选"] = [q for q in QUESTIONS if q["question_type"] == "多选"]
    pool["填空_高中物理"] = [q for q in QUESTIONS if q["type"] == "高中物理" and q["question_type"] == "填空"]
    pool["填空_地理常识"] = [q for q in QUESTIONS if q["type"] == "地理常识" and q["question_type"] == "填空"]
    pool["填空_文学常识"] = [q for q in QUESTIONS if q["type"] == "文学常识" and q["question_type"] == "填空"]
    all_types = set(q["type"] for q in QUESTIONS)
    for t in sorted(all_types):
        pool[f"train_{t}"] = [q for q in QUESTIONS if q["type"] == t]
    _PRE_COMPUTED_POOLS = pool
    _LAST_POOL_REFRESH = time.time()

def get_pool(name):
    """获取预计算池，带自动刷新（每5分钟刷新一次）"""
    if not _PRE_COMPUTED_POOLS or time.time() - _LAST_POOL_REFRESH > 300:
        _refresh_pools()
    return _PRE_COMPUTED_POOLS.get(name, [])

# 启动时预计算
_refresh_pools()

@app.get("/api/exam/generate")
def generate_exam():
    """生成一套模拟考试试卷"""
    selected = []
    qid_offset = 0

    # 1. 单选（使用预计算池）
    for qtype, count in EXAM_CONFIG["单选"]:
        pool = get_pool(qtype)
        if not pool:
            continue
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

    # 2. 多选（使用预计算池）
    multi_pool = get_pool("多选")
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


# 防止重复出题：记录已出过的题ID，按题型轮换
_used_tracker: dict[str, set[int]] = {}


def _pick_questions(pool, need: int, type_key: str):
    """优先选没出过的，该题型轮完一遍就重置重新开始"""
    global _used_tracker
    used = _used_tracker.setdefault(type_key, set())
    fresh = [q for q in pool if q["id"] not in used]
    if len(fresh) < need:
        # 该题型轮完一遍，全部重置重新抽
        used.clear()
        fresh = pool[:]
    chosen = random.sample(fresh, need)
    used.update(q["id"] for q in chosen)
    return chosen


@app.get("/api/exam/generate_gt")
def generate_gt_exam():
    """生成广铁限时模拟题（按顺序：37单选→4多选→4填空，不重复）"""
    # 缓存Key基于时间+题库哈希，5秒内同一时间段的请求共享一份试卷
    today = time.strftime("%Y%m%d%H%M")
    cache_key = f"gt_{today[:10]}"
    cached = exam_cache.get(cache_key)
    if cached:
        return cached

    selected = []
    qid_offset = 0

    # 1. 单选（使用预计算池）
    for qtype, count in EXAM_CONFIG["单选"]:
        pool = get_pool(qtype)
        if not pool:
            continue
        chosen = _pick_questions(pool, min(count, len(pool)), qtype)
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
    multi_pool = get_pool("多选")
    for q in _pick_questions(multi_pool, EXAM_CONFIG["多选"], "多选"):
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item:
            del item["answer"]
        if "analysis" in item:
            del item["analysis"]
        selected.append(item)
        qid_offset += 1

    # 3. 填空（2物理+1地理+1文学）- 使用预计算池
    for q in _pick_questions(get_pool("填空_高中物理"), 2, "填空_高中物理"):
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item: del item["answer"]
        if "analysis" in item: del item["analysis"]
        selected.append(item)
        qid_offset += 1
    for q in _pick_questions(get_pool("填空_地理常识"), 1, "填空_地理常识"):
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item: del item["answer"]
        if "analysis" in item: del item["analysis"]
        selected.append(item)
        qid_offset += 1
    for q in _pick_questions(get_pool("填空_文学常识"), 1, "填空_文学常识"):
        item = dict(q)
        item["exam_index"] = qid_offset + 1
        if "answer" in item: del item["answer"]
        if "analysis" in item: del item["analysis"]
        selected.append(item)
        qid_offset += 1

    # 记录本次用过的题（已由pick函数内部记录）

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
    """获取所有可训练的类型"""
    seen = set()
    for q in QUESTIONS:
        if q["question_type"] in ("单选", "多选"):
            seen.add(q["type"])
    type_order = ["图形推理", "数字推理", "言语理解", "文学常识", "地理常识", "数学物理", "高中数学", "高中物理"]
    result = [t for t in type_order if t in seen]
    return {"code": 0, "data": result}


@app.get("/api/train/questions")
def get_train_questions(
    type_name: str = Query(alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(1, ge=1, le=5),
):
    """获取分层训练题目（不返回总数量）"""
    pool = get_pool(f"train_{type_name}")
    filtered = [q for q in pool if q["question_type"] in ("单选", "多选")]
    if not filtered:
        return {"code": 0, "data": {"items": [], "has_more": False}}

    # 排序后切片（不shuffle，保证分页不重复）
    filtered.sort(key=lambda x: x["id"])

    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    has_more = end < len(filtered)
    total = len(filtered)

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
            "total": total,
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
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:linear-gradient(135deg,#f0f4ff 0%,#f5f0ff 50%,#fff0f5 100%);color:#2c3e50;min-height:100vh;background-attachment:fixed}
/* === 首页 === */
.home-page{max-width:800px;margin:0 auto;padding:60px 24px 40px;animation:fadeIn .6s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.home-title{font-size:30px;font-weight:800;background:linear-gradient(135deg,#1a73e8,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:6px;letter-spacing:-0.5px}
.home-sub{text-align:center;color:#888;font-size:14px;margin-bottom:8px}
.home-cards{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:28px}
.home-card{background:rgba(255,255,255,0.9);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:20px;padding:32px 24px;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.06);transition:all 0.4s cubic-bezier(0.34,1.56,0.64,1);text-align:center;border:1px solid rgba(255,255,255,0.8);position:relative;overflow:hidden}
.home-card::before{content:'';position:absolute;top:0;left:0;right:0;height:4px}
.home-card:hover{transform:translateY(-6px) scale(1.02);box-shadow:0 12px 40px rgba(0,0,0,0.12)}
.home-card:active{transform:scale(0.97)}
.home-card .icon{font-size:52px;margin-bottom:14px;display:block;transition:transform 0.3s}
.home-card:hover .icon{transform:scale(1.15) rotate(-5deg)}
.home-card .name{font-size:19px;font-weight:700;color:#1a1a2e;margin-bottom:8px}
.home-card .desc{font-size:13px;color:#8e8ea0;line-height:1.7}
.home-card.exam{border:1px solid rgba(233,30,99,0.15)}.home-card.exam::before{background:linear-gradient(90deg,#e91e63,#ff6b6b)}
.home-card.train{border:1px solid rgba(26,115,232,0.15)}.home-card.train::before{background:linear-gradient(90deg,#1a73e8,#8b5cf6)}
.home-footer{text-align:center;margin-top:36px}
.home-footer .btn{display:inline-flex;align-items:center;gap:6px;padding:10px 24px;border:1px solid #e8e8e8;border-radius:24px;color:#666;font-size:13px;cursor:pointer;background:rgba(255,255,255,0.9);transition:all 0.3s;backdrop-filter:blur(10px)}
.home-footer .btn:hover{background:#fff;border-color:#d0d0d0;box-shadow:0 4px 12px rgba(0,0,0,0.06);transform:translateY(-2px)}
.blessing{text-align:center;margin:18px auto 0;padding:12px 16px;max-width:360px;font-size:14px;color:#e91e63;font-weight:500;background:linear-gradient(135deg,#fff0f5,#fce4ec);border-radius:14px;border:1px solid #f8bbd0;letter-spacing:1px;animation:pulseGlow 2s ease-in-out infinite}
@keyframes pulseGlow{0%,100%{box-shadow:0 0 0 0 rgba(233,30,99,0.1)}50%{box-shadow:0 0 20px 4px rgba(233,30,99,0.15)}}
/* === Header === */
.header{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);color:#fff;padding:0 20px;height:54px;display:flex;align-items:center;position:fixed;top:0;left:0;right:0;z-index:100;box-shadow:0 2px 20px rgba(0,0,0,0.2)}
.header .back{background:rgba(255,255,255,0.1);border:none;color:#fff;font-size:20px;cursor:pointer;padding:6px 10px;margin-right:10px;display:flex;align-items:center;border-radius:10px;transition:all 0.2s}
.header .back:hover{background:rgba(255,255,255,0.2);transform:scale(1.05)}
.header .title{font-size:16px;font-weight:600;flex:1;letter-spacing:0.5px}
.header .right{font-size:13px;display:flex;align-items:center;gap:10px}
.timer-badge{background:rgba(255,255,255,0.12);padding:5px 14px;border-radius:14px;font-variant-numeric:tabular-nums;font-size:14px;font-weight:600;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.08)}
/* === Layout === */
.page{display:none;padding-top:54px;min-height:100vh}
.page.active{display:block;animation:pageIn .35s ease}
@keyframes pageIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.content{padding:16px;max-width:820px;margin:0 auto}
/* === 分层训练选题卡片 === */
.train-header{background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:18px;padding:30px 24px;color:#fff;margin-bottom:20px;text-align:center;position:relative;overflow:hidden}
.train-header::after{content:'';position:absolute;top:-50%;left:-50%;right:-50%;bottom:-50%;background:radial-gradient(circle at 30% 70%,rgba(139,92,246,0.15) 0%,transparent 50%),radial-gradient(circle at 70% 30%,rgba(26,115,232,0.1) 0%,transparent 50%);pointer-events:none}
.train-header .big{font-size:26px;font-weight:700;margin-bottom:4px;position:relative}
.train-header .small{font-size:14px;opacity:0.75;position:relative}
.type-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:0 0 20px}
.type-btn{background:rgba(255,255,255,0.95);border-radius:18px;padding:22px 16px 18px;text-align:center;cursor:pointer;transition:all 0.35s cubic-bezier(0.34,1.56,0.64,1);box-shadow:0 2px 12px rgba(0,0,0,0.06);position:relative;overflow:hidden;border:1px solid rgba(255,255,255,0.8)}
.type-btn:hover{transform:translateY(-4px) scale(1.02);box-shadow:0 12px 28px rgba(0,0,0,0.1)}
.type-btn:active{transform:scale(0.94)}
.type-btn .t-icon{font-size:38px;display:block;margin-bottom:8px;transition:transform 0.3s}
.type-btn:hover .t-icon{transform:scale(1.2) rotate(-8deg)}
.type-btn .t-name{font-size:15px;font-weight:600;color:#1a1a2e;margin-bottom:3px}
.type-btn .t-count{font-size:12px;color:#999}
.type-btn .t-bar{position:absolute;bottom:0;left:0;right:0;height:5px;border-radius:0 0 18px 18px}
.type-btn[data-type="图形推理"] .t-bar{background:linear-gradient(90deg,#667eea,#764ba2)}
.type-btn[data-type="数字推理"] .t-bar{background:linear-gradient(90deg,#4facfe,#00f2fe)}
.type-btn[data-type="言语理解"] .t-bar{background:linear-gradient(90deg,#43e97b,#38f9d7)}
.type-btn[data-type="高中数学"] .t-bar{background:linear-gradient(90deg,#fa709a,#fee140)}
.type-btn[data-type="高中物理"] .t-bar{background:linear-gradient(90deg,#f093fb,#f5576c)}
.type-btn[data-type="铁道信号"] .t-bar{background:linear-gradient(90deg,#4facfe,#00f2fe)}
.type-btn[data-type="文学常识"] .t-bar{background:linear-gradient(90deg,#a18cd1,#fbc2eb)}
.type-btn[data-type="地理常识"] .t-bar{background:linear-gradient(90deg,#84fab0,#8fd3f4)}
/* 题目导航 */
.train-progress{background:rgba(255,255,255,0.9);backdrop-filter:blur(10px);border-radius:14px;padding:14px 18px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,0.04);display:flex;align-items:center;gap:12px;border:1px solid rgba(255,255,255,0.8)}
.train-progress .p-bar{flex:1;height:6px;background:#e8e8e8;border-radius:3px;overflow:hidden}
.train-progress .p-bar .p-fill{height:100%;background:linear-gradient(90deg,#667eea,#764ba2);border-radius:3px;transition:width 0.5s cubic-bezier(0.34,1.56,0.64,1)}
.train-progress .p-text{font-size:13px;color:#888;white-space:nowrap;font-variant-numeric:tabular-nums}
.train-progress .p-type{font-size:11px;padding:4px 12px;border-radius:10px;background:rgba(102,126,234,0.12);color:#667eea;font-weight:600;white-space:nowrap}
/* === Question Card === */
.q-card{background:rgba(255,255,255,0.95);backdrop-filter:blur(20px);border-radius:16px;box-shadow:0 2px 16px rgba(0,0,0,0.06);padding:22px;margin-bottom:14px;border:1px solid rgba(255,255,255,0.8);transition:transform 0.2s}
.q-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:6px}
.q-num{font-size:13px;color:#888}
.q-num .n{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;background:linear-gradient(135deg,#1a73e8,#8b5cf6);color:#fff;border-radius:50%;font-size:12px;font-weight:700;margin-right:4px}
.q-type{font-size:11px;padding:3px 12px;border-radius:12px;font-weight:600}
.q-type[data-t="单选"]{background:#e8f0fe;color:#1a73e8}
.q-type[data-t="多选"]{background:#fce4ec;color:#e91e63}
.q-type[data-t="填空"]{background:#e8f5e9;color:#4caf50}
.q-text{font-size:15px;line-height:1.8;margin-bottom:16px;white-space:pre-wrap;color:#2c3e50}
.q-img-wrap{margin:10px 0;text-align:center}.q-img-wrap img{max-width:100%;max-height:300px;border-radius:10px;border:1px solid #eee;background:#fafafa;box-shadow:0 2px 8px rgba(0,0,0,0.04)}
.q-img-full{margin:10px 0;text-align:center}.q-img-full img{max-width:100%;width:100%;border-radius:10px;border:1px solid #eee;background:#fafafa;box-shadow:0 2px 8px rgba(0,0,0,0.04)}
/* Options */
.options{display:flex;flex-direction:column;gap:8px}
.option{display:flex;align-items:flex-start;gap:10px;padding:13px 16px;border:2px solid #eaeef5;border-radius:12px;cursor:pointer;transition:all 0.25s cubic-bezier(0.34,1.56,0.64,1);font-size:14px;line-height:1.6;background:#fff}
.option:hover{border-color:#b3d4fc;background:#f7faff;transform:translateX(4px)}
.option.selected{border-color:#1a73e8;background:#eef4ff;box-shadow:0 0 0 3px rgba(26,115,232,0.1)}
.option.correct{border-color:#4caf50;background:#f1faf1;box-shadow:0 0 0 3px rgba(76,175,80,0.1)}
.option.wrong{border-color:#f44336;background:#fff5f5;box-shadow:0 0 0 3px rgba(244,67,54,0.1)}
.option .letter{width:26px;height:26px;border-radius:50%;background:#f0f2f5;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;transition:all 0.2s;color:#555}
.option.selected .letter{background:linear-gradient(135deg,#1a73e8,#8b5cf6);color:#fff}
.option.correct .letter{background:linear-gradient(135deg,#4caf50,#66bb6a);color:#fff}
.option.wrong .letter{background:linear-gradient(135deg,#f44336,#ef5350);color:#fff}
/* 填空题输入 */
.fill-input{width:100%;padding:13px 18px;border:2px solid #e0e4ea;border-radius:12px;font-size:16px;outline:none;transition:all 0.2s;background:#fff}
.fill-input:focus{border-color:#1a73e8;box-shadow:0 0 0 3px rgba(26,115,232,0.1)}
.fill-input.correct{border-color:#4caf50;background:#f1faf1;box-shadow:0 0 0 3px rgba(76,175,80,0.1)}
.fill-input.wrong{border-color:#f44336;background:#fff5f5;box-shadow:0 0 0 3px rgba(244,67,54,0.1)}
/* Analysis */
.analysis-box{background:linear-gradient(135deg,#fffbe6,#fff8e1);border:1px solid #ffe082;border-radius:12px;padding:16px;margin-top:14px;font-size:14px;color:#7c6a00;line-height:1.7}
.analysis-box .label{font-weight:700;color:#f57f17}
.analysis-box.correct{background:linear-gradient(135deg,#f1faf1,#e8f5e9);border-color:#a5d6a7;color:#2e7d32}
.analysis-box.correct .label{color:#2e7d32}
/* Buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:14px 30px;border:none;border-radius:12px;font-size:15px;font-weight:600;cursor:pointer;transition:all 0.3s cubic-bezier(0.34,1.56,0.64,1);text-align:center}
.btn:active{transform:scale(0.95)}
.btn-primary{background:linear-gradient(135deg,#1a73e8,#8b5cf6);color:#fff;box-shadow:0 4px 14px rgba(26,115,232,0.3)}
.btn-primary:hover{box-shadow:0 6px 20px rgba(26,115,232,0.4);transform:translateY(-2px)}
.btn-primary:disabled{background:#c0c8d8;box-shadow:none;cursor:not-allowed;transform:none}
.btn-success{background:linear-gradient(135deg,#4caf50,#66bb6a);color:#fff;box-shadow:0 4px 14px rgba(76,175,80,0.3)}
.btn-success:hover{box-shadow:0 6px 20px rgba(76,175,80,0.4);transform:translateY(-2px)}
.btn-warning{background:linear-gradient(135deg,#ff6b35,#ff8a65);color:#fff;box-shadow:0 4px 14px rgba(255,107,53,0.3)}
.btn-warning:hover{box-shadow:0 6px 20px rgba(255,107,53,0.4);transform:translateY(-2px)}
.btn-outline{background:#fff;color:#555;border:1px solid #ddd}
.btn-outline:hover{background:#f7f8fa;border-color:#ccc;transform:translateY(-2px)}
.btn-block{display:flex;width:100%}
.btn-sm{padding:10px 20px;font-size:13px;border-radius:10px}
/* Exam footer */
.exam-footer{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
.exam-footer .btn{flex:1;min-width:120px}
/* Exam layout */
.exam-wrap{max-width:720px;margin:0 auto;position:relative}
.exam-main{flex:1;min-width:0}
/* === 成绩页 === */
.result-card{background:rgba(255,255,255,0.95);backdrop-filter:blur(20px);border-radius:20px;padding:36px 28px;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,0.06);margin-bottom:20px;border:1px solid rgba(255,255,255,0.8);animation:resultIn .6s ease}
@keyframes resultIn{from{opacity:0;transform:scale(0.9)}to{opacity:1;transform:scale(1)}}
.result-score{font-size:72px;font-weight:800;background:linear-gradient(135deg,#1a73e8,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:12px 0}
.result-score .unit{font-size:24px;-webkit-text-fill-color:#999;background:none}
.result-label{font-size:15px;color:#888;margin-bottom:4px}
.result-info{font-size:14px;color:#666;margin-bottom:16px;line-height:1.8;background:#f8f9fa;border-radius:12px;padding:14px 20px;display:inline-block}
.result-actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.result-actions .btn{min-width:140px}
.result-detail-item{padding:12px 16px;margin:6px 0;border-radius:12px;font-size:13px;display:flex;justify-content:space-between;align-items:center;transition:transform 0.2s}
.result-detail-item:hover{transform:translateX(4px)}
.result-detail-item.correct{background:linear-gradient(135deg,#e8f5e9,#f1faf1);color:#2e7d32;border-left:3px solid #4caf50}
.result-detail-item.wrong{background:linear-gradient(135deg,#ffebee,#fff5f5);color:#c62828;border-left:3px solid #f44336}
/* Score ring */
.score-ring{width:140px;height:140px;border-radius:50%;margin:0 auto 8px;position:relative;display:flex;align-items:center;justify-content:center}
.score-ring svg{transform:rotate(-90deg)}
.score-ring .ring-bg{fill:none;stroke:#e8ecf0;stroke-width:8}
.score-ring .ring-fill{fill:none;stroke:url(#scoreGrad);stroke-width:8;stroke-linecap:round;stroke-dasharray:377;stroke-dashoffset:377;transition:stroke-dashoffset 1.5s cubic-bezier(0.34,1.56,0.64,1)}
/* Stats grid */
.stats-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:16px 0 24px}
.stat-box{background:#f8f9fa;border-radius:14px;padding:14px 8px;text-align:center;border:1px solid #eee}
.stat-box .num{font-size:22px;font-weight:700;color:#1a73e8}
.stat-box .num.green{color:#4caf50}
.stat-box .num.red{color:#f44336}
.stat-box .lbl{font-size:12px;color:#888;margin-top:4px}
/* Wrong book */
.wrong-item{background:rgba(255,255,255,0.95);backdrop-filter:blur(10px);border-radius:16px;padding:20px;margin-bottom:12px;box-shadow:0 2px 12px rgba(0,0,0,0.04);border:1px solid rgba(255,255,255,0.8);transition:transform 0.2s}
.wrong-item:hover{transform:translateX(4px)}
.wrong-empty{text-align:center;padding:60px 20px;color:#999}
.wrong-empty .icon{font-size:56px;margin-bottom:16px;display:block}
/* 多选标签 */
.multi-hint{font-size:12px;color:#e91e63;margin-bottom:8px;font-weight:600;display:flex;align-items:center;gap:4px}
/* Scrollbar */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(0,0,0,0.15);border-radius:3px}
.submit-top-btn{display:inline-flex;align-items:center;gap:4px;padding:7px 16px;background:linear-gradient(135deg,#e74c3c,#f44336);color:#fff;border:none;border-radius:10px;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.3s;box-shadow:0 2px 8px rgba(231,76,60,0.3)}
.submit-top-btn:hover{transform:translateY(-1px);box-shadow:0 4px 14px rgba(231,76,60,0.4)}
/* === Mobile === */
@media(max-width:640px){
.home-cards{grid-template-columns:1fr;gap:14px}
.home-page{padding:40px 14px 20px}
.home-title{font-size:26px}
.type-grid{grid-template-columns:1fr 1fr;gap:10px}
.content{padding:12px}
.q-card{padding:16px}
.result-score{font-size:52px}
.stats-grid{gap:8px}
.stat-box .num{font-size:18px}
.exam-footer{flex-direction:column}
.exam-footer .btn{min-width:auto}
.exam-wrap{flex-direction:column}
.score-ring{width:110px;height:110px}
.btn{padding:12px 20px;font-size:14px}
}
/* Exam question nav - horizontal scrollable strip */
.q-nav-strip{display:flex;gap:4px;padding:8px 4px;overflow-x:auto;overflow-y:hidden;white-space:nowrap;scrollbar-width:thin;scrollbar-color:#c0c4cc transparent;min-height:36px;align-items:center}
.q-nav-strip::-webkit-scrollbar{height:3px}
.q-nav-strip::-webkit-scrollbar-thumb{background:#c0c4cc;border-radius:2px}
.q-nav-item{width:26px;min-width:26px;height:26px;border-radius:50%;border:1.5px solid #e0e4ea;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;cursor:pointer;transition:all .2s;color:#999;background:#fff}
.q-nav-item:hover{border-color:#1a73e8;color:#1a73e8;transform:scale(1.12)}
.q-nav-item.answered{background:#34a853;border-color:#34a853;color:#fff}
.q-nav-item.active{background:#1a73e8;border-color:#1a73e8;color:#fff;transform:scale(1.15);box-shadow:0 2px 8px rgba(26,115,232,0.3)}
.nav-label{font-size:12px;color:#666;margin-bottom:4px}
.q-dot.active{border-color:#1a73e8;background:#1a73e8;color:#fff}
.q-dot.answered{border-color:#4caf50;background:#e8f5e9;color:#4caf50}
.q-dot.wrong-dot{border-color:#f44336;background:#ffebee;color:#f44336}
.q-dot.correct-dot{border-color:#4caf50;background:#e8f5e9;color:#4caf50}
</style>
</head>
<body>

<!-- ========== 首页 ========== -->
<div id="pageHome" class="page active">
  <div class="home-page">
    <div class="home-title">广铁机考模拟题库</div>
    <div class="home-sub">广州铁路局机考模拟 · 分层训练</div>
    <div class="blessing">祝考试顺利，成功上岸</div>
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
    <div style="text-align:center;margin-top:24px;font-size:12px;color:#bbb">铁路校招 · 备考助手</div>
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
let _wrongBatchTimer = null;
function _flushWrongBatch() {
  _wrongBatchTimer = null;
  localStorage.setItem('wrong_ids', JSON.stringify(getWrongIds()));
}
function addWrongId(id) {
  let ids = getWrongIds();
  if (!ids.includes(id)) { ids.push(id); }
  if(_wrongBatchTimer) clearTimeout(_wrongBatchTimer);
  _wrongBatchTimer = setTimeout(_flushWrongBatch, 300);
}
function removeWrongId(id) {
  let ids = getWrongIds().filter(i => i !== id);
  localStorage.setItem('wrong_ids', JSON.stringify(ids));
  if(_wrongBatchTimer) clearTimeout(_wrongBatchTimer);
}

function loadWrongBook() {
  const el = document.getElementById('wrongContent');
  const ids = getWrongIds();
  if (ids.length === 0) {
    el.innerHTML = '<div class="wrong-empty"><div class="icon">🎉</div><p>暂无错题记录</p><p style="font-size:13px;margin-top:8px">继续加油练习吧！</p></div>';
    return;
  }
  el.innerHTML = '<div style="text-align:center;padding:20px;color:#999">加载中...</div>';
  fetch('/exam/api/wrong/list', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})})
    .then(r=>r.json()).then(res=>{
      if(res.code!==0||!res.data.items.length){el.innerHTML='<div class="wrong-empty"><p>暂无错题</p></div>';return}
      let html = '<div style="margin:16px 0;text-align:right"><button class="btn btn-sm btn-outline" onclick="clearWrongBook()">清空错题本</button></div>';
      res.data.items.forEach(q=>{
        html += '<div class="wrong-item">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">';
        html += '<span style="font-size:12px;color:#888">'+q.type+' · '+q.question_type+'</span>';
        html += '<span style="font-size:12px;color:#f44336;cursor:pointer" onclick="removeWrongId('+q.id+');loadWrongBook()">✕ 移除</span>';
        html += '</div>';
        html += '<div style="font-size:14px;line-height:1.8;white-space:pre-wrap;margin-bottom:10px">'+htmlEscape(q.question)+'</div>';
      if(q.image && q.type==='图形推理'){
        html += '<div class="q-img-full"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
      }
      if(q.image && q.type!=='图形推理'){
        html += '<div class="q-img-wrap"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
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
  fetch('/exam/api/exam/generate_gt').then(r=>r.json()).then(res=>{
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
  let navHtml = '<div class="q-nav-strip" id="qNavStrip">';
  examData.items.forEach((q,i)=>{
    html += '<div class="q-card" id="eq_'+i+'">';
    html += '<div class="q-header">';
    html += '<span class="q-num">第 <span class="n">'+(i+1)+'</span> 题</span>';
    html += '<span class="q-type" data-t="'+q.question_type+'">'+q.type+' · '+(q.question_type==='单选'?'单选题':q.question_type==='多选'?'多选题':'填空题')+'</span>';
    html += '</div>';
    html += '<div class="q-text">'+htmlEscape(q.question)+'</div>';
    if(q.image && q.type==='图形推理'){
      html += '<div class="q-img-full"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
    }
    if(q.image && q.type!=='图形推理'){
      html += '<div class="q-img-wrap"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
    }
    if(q.question_type==='填空'){
      html += '<input class="fill-input" id="exam_inp_'+i+'" placeholder="请输入答案" onchange="examAnswers['+q.id+']={id:'+q.id+',selected:this.value};updateNavStrip()">';
    } else {
      if(q.question_type==='多选') html += '<div class="multi-hint">📌 多选（可点击多个选项）</div>';
      html += '<div class="options" id="exam_opts_'+i+'">';
      Object.entries(q.options||{}).forEach(([k,v])=>{
        html += '<div class="option" onclick="examSelectOpt(this,'+q.id+',\''+k+'\','+(q.question_type==='多选'?'true':'false')+')" data-idx="'+i+'">';
        html += '<span class="letter">'+k+'</span>';
        html += '<span>'+htmlEscape(v)+'</span></div>';
      });
      html += '</div>';
    }
    html += '</div>';
    navHtml += '<span class="q-nav-item" id="qn_'+i+'" onclick="document.getElementById(\'eq_'+i+'\').scrollIntoView({behavior:\'smooth\',block:\'center\'});hilitNav('+i+')">'+(i+1)+'</span>';
  });
  navHtml += '</div>';
  html += '<div style="margin:12px 0 8px"><div class="nav-label">📋 题目导航</div>'+navHtml+'</div>';
  html += '<div class="exam-footer">';
  html += '<button class="btn btn-primary btn-block" onclick="submitExam()" id="examSubmitBtn">提交试卷</button>';
  html += '</div>';
  el.innerHTML = html;
}

function updateNavStrip(){
  if(!examData||!examData.items) return;
  examData.items.forEach((q,i)=>{
    const nav = document.getElementById('qn_'+i);
    if(!nav) return;
    const ans = examAnswers[q.id];
    if(ans && ans.selected && ans.selected.toString().trim()){
      nav.className = 'q-nav-item answered';
    } else {
      nav.className = 'q-nav-item';
    }
  });
}

function hilitNav(i){
  document.querySelectorAll('.q-nav-item.active').forEach(el=>el.classList.remove('active'));
  const el = document.getElementById('qn_'+i);
  if(el) el.classList.add('active');
}

// 选答案 - 用DOM参数传递避免重复查询
window.examSelectOpt = function(el, qid, opt, isMulti) {
  currentExamQuestion = el.dataset.idx;
  
  if(isMulti){
    el.classList.toggle('selected');
    const selected = [];
    el.parentElement.querySelectorAll('.option.selected').forEach(o=>{
      const letter = o.querySelector('.letter');
      if(letter) selected.push(letter.textContent.trim());
    });
    examAnswers[qid] = {id:qid, selected: selected.join(',')};
  } else {
    el.parentElement.querySelectorAll('.option').forEach(o=>o.classList.remove('selected'));
    el.classList.add('selected');
    examAnswers[qid] = {id:qid, selected: opt};
  }
  updateNavStrip();
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
  fetch('/exam/api/exam/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answers,time_used:timeUsed})})
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
  
  let correctCount = data.details.filter(d=>d.correct).length;
  let wrongCount = data.details.length - correctCount;
  let unansweredCount = data.details.filter(d=> !d.user_answer || d.user_answer==='').length;
  const pct = Math.round(data.total_score / data.full_score * 100);
  const ringDash = 377 * (1 - pct / 100);
  
  // SVG圆环 + 分数卡
  let html = '<div class="result-card">';
  html += '<div style="margin-bottom:4px;font-size:15px;color:#888;letter-spacing:2px;font-weight:500">成 绩</div>';
  html += '<div class="score-ring">';
  html += '<svg width="140" height="140" viewBox="0 0 140 140">';
  html += '<defs><linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#1a73e8"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>';
  html += '<circle class="ring-bg" cx="70" cy="70" r="60"/>';
  html += '<circle class="ring-fill" cx="70" cy="70" r="60" style="stroke-dashoffset:'+ringDash+'"/>';
  html += '</svg>';
  html += '<div style="position:absolute;text-align:center"><div class="result-score">'+data.total_score+'<span class="unit">/'+data.full_score+'</span></div></div>';
  html += '</div>';
  html += '<div class="result-label">'+pct+'% 正确率</div>';
  html += '<div class="result-info">用时 '+Math.floor(data.time_used/60)+'分'+data.time_used%60+'秒</div>';
  // Stats grid
  html += '<div class="stats-grid">';
  html += '<div class="stat-box"><div class="num">'+data.details.length+'</div><div class="lbl">总题数</div></div>';
  html += '<div class="stat-box"><div class="num green">'+correctCount+'</div><div class="lbl">正确</div></div>';
  html += '<div class="stat-box"><div class="num red">'+wrongCount+'</div><div class="lbl">错误</div></div>';
  html += '</div>';
  html += '</div>';
  
  // 按钮组
  html += '<div class="result-actions">';
  html += '<button class="btn btn-success" onclick="backHome();setTimeout(startGTExam,100)">再来一套</button>';
  html += '</div>';
  
  // 查看模式切换
  html += '<div style="display:flex;gap:8px;margin-bottom:12px;padding:12px 0;border-bottom:2px solid #eee">';
  html += '<button id="filterBtnAll" class="btn btn-sm btn-primary" onclick="switchExamFilter(\'all\')" style="flex:1">📋 全部 ('+data.details.length+'题)</button>';
  html += '<button id="filterBtnWrong" class="btn btn-sm btn-outline" onclick="switchExamFilter(\'wrong\')" style="flex:1">❌ 仅错题 ('+wrongCount+'题)</button>';
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
    
    html += '<div class="result-detail-item '+(isCorrect?'correct':'wrong')+'" data-correct="'+isCorrect+'">';
    html += '<div><b>第 '+(i+1)+' 题</b> <span style="font-size:11px;color:#999">'+q.type+'</span></div>';
    html += '<div>'+(isCorrect?'✅ +'+d.score+'分':'❌ 0分')+'</div></div>';
    html += '<div class="q-text">'+htmlEscape(q.question)+'</div>';
    if(q.image && q.type==='图形推理'){
      html += '<div class="q-img-full"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
    } else if(q.image){
      html += '<div class="q-img-wrap"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
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
  
  // 显示/隐藏对应题目，无需重新渲染
  document.querySelectorAll('#reviewSection .result-item').forEach(el=>{
    el.style.display = (mode==='all' || el.dataset.correct==='false') ? '' : 'none';
  });
}
// ========== 分层训练 ==========
var trainType = '';
var trainPage = 1;

function loadTypes() {
  const el = document.getElementById('trainContent');
  el.innerHTML = '<div style="text-align:center;padding:40px 0;color:#999">加载中...</div>';
  fetch('/exam/api/train/types').then(r=>r.json()).then(res=>{
    if(res.code!==0||!res.data.length){el.innerHTML='<div style="padding:20px;text-align:center;color:#999">暂无题目</div>';return}
    // 题型图标映射
    const icons = {'图形推理':'🧩','数字推理':'🔢','言语理解':'💬','高中数学':'📐','高中物理':'⚡','铁道信号':'🚊'};
    let html = '<div class="train-header"><div class="big">📚 分层训练</div><div class="small">选择练习题型，逐项突破</div></div>';
    html += '<div class="type-grid">';
    res.data.forEach(t=>{
      html += '<div class="type-btn" data-type="'+t+'" onclick="startTrainType(\''+t+'\')">';
      html += '<span class="t-icon">'+(icons[t]||'📖')+'</span>';
      html += '<span class="t-name">'+t+'</span>';
      html += '<span class="t-count">点击开始练习 →</span>';
      html += '<div class="t-bar"></div></div>';
    });
    html += '</div>';
    el.innerHTML = html;
  }).catch(()=>{});
}

function startTrainType(type) {
  trainType = type;
  trainPage = 1;
  trainCache = {};   // 切换题型时清空缓存
  trainTotal = 0;
  showPage('pageTrain');
  loadTrainQuestion();
}

function loadTrainQuestion() {
  // 如果该页已缓存，直接渲染（不请求API）
  if(trainCache[trainPage]){
    const cached = trainCache[trainPage];
    renderTrainQuestion(cached.q, cached.hasMore, cached.total, true);
    return;
  }
  const el = document.getElementById('trainContent');
  el.innerHTML = '<div style="text-align:center;padding:40px 0;color:#999">加载中...</div>';
  fetch('/exam/api/train/questions?type='+encodeURIComponent(trainType)+'&page='+trainPage+'&page_size=1')
    .then(r=>r.json()).then(res=>{
      if(res.code!==0||!res.data.items.length){
        el.innerHTML = '<div style="padding:40px;text-align:center"><p style="color:#888;margin-bottom:20px">没有更多题目了</p><button class="btn btn-outline btn-sm" onclick="loadTypes()">返回题型列表</button></div>';
        return;
      }
      trainTotal = res.data.total || 0;
      const q = res.data.items[0];
      // 缓存题目数据（不含答案）
      trainCache[trainPage] = {q: q, hasMore: res.data.has_more, total: trainTotal, selected: null, result: null};
      renderTrainQuestion(q, res.data.has_more, trainTotal, false);
    }).catch(()=>{});
}

var currentTrainQ = null;
var trainCache = {};   // 缓存已答题目和结果 {page: {q, selected, result, hasMore}}
var trainTotal = 0;    // 当前题型总题数

function renderTrainQuestion(q, hasMore, total, fromCache) {
  currentTrainQ = q;
  const el = document.getElementById('trainContent');
  const pct = total > 0 ? Math.min(Math.round(trainPage/total*100), 100) : 0;
  // 进度条 + 导航
  let html = '<div class="train-progress">';
  html += '<div class="p-type">'+trainType+'</div>';
  html += '<div class="p-bar"><div class="p-fill" style="width:'+pct+'%"></div></div>';
  html += '<span class="p-text">'+trainPage+'/'+total+'</span></div>';
  // 导航按钮行
  html += '<div style="display:flex;gap:8px;margin-bottom:10px">';
  if(trainPage > 1) html += '<button class="btn btn-sm" onclick="prevTrain()" style="flex:1;background:#f0f0f0;color:#555;border:1px solid #ddd;border-radius:10px">&larr; 上一题</button>';
  else html += '<div style="flex:1"></div>';
  if(hasMore) html += '<button class="btn btn-sm" onclick="nextTrain()" style="flex:1;background:#667eea;color:#fff;border:none;border-radius:10px">下一题 &rarr;</button>';
  else html += '<div style="flex:1"></div>';
  html += '</div>';
  // 题目卡片
  html += '<div class="q-card">';
  html += '<div class="q-header">';
  html += '<span class="q-num">第 <span class="n">'+(trainPage)+'</span> 题</span>';
  html += '<span class="q-type">'+(q.question_type==='多选'?'多选题':'单选题')+'</span>';
  html += '</div>';
  html += '<div class="q-text">'+htmlEscape(q.question)+'</div>';
  if(q.image && q.type==='图形推理'){
  html += '<div class="q-img-full"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
    }
    if(q.image && q.type!=='图形推理'){
  html += '<div class="q-img-wrap"><img src="./static/'+q.image[0]+'" alt="题图" loading="lazy"></div>';
    }
  if(q.options){
    if(q.question_type==='多选') html += '<div class="multi-hint">多选（可点击多个选项）</div>';
    html += '<div class="options" id="trainOpts">';
    Object.entries(q.options).forEach(([k,v])=>{
      html += '<div class="option" onclick="trainSelectOpt(this,\''+k+'\','+(q.question_type==='多选'?'true':'false')+')">';
      html += '<span class="letter">'+k+'</span>';
      html += '<span>'+htmlEscape(v)+'</span></div>';
    });
    html += '</div>';
  }
  html += '<div id="trainResult" style="margin-top:12px"></div>';
  html += '<div style="display:flex;gap:10px;margin-top:14px">';
  html += '<button class="btn btn-primary" style="flex:1;padding:12px 0" id="trainSubmitBtn" onclick="submitTrain()">提交答案</button>';
  html += '</div></div>';
  el.innerHTML = html;
  window.trainSelected = q.question_type==='多选'?[]:'';
  
  // 如果从缓存回来，恢复答案和结果
  if(fromCache && trainCache[trainPage]){
    const cached = trainCache[trainPage];
    if(cached.selected !== null){
      window.trainSelected = cached.selected;
      // 恢复选项高亮
      const opts = document.getElementById('trainOpts');
      if(opts){
        if(Array.isArray(cached.selected)){
          opts.querySelectorAll('.option').forEach(o=>{
            const letter = o.querySelector('.letter').textContent;
            if(cached.selected.includes(letter)) o.classList.add('selected');
          });
        } else if(cached.selected){
          opts.querySelectorAll('.option').forEach(o=>{
            if(o.querySelector('.letter').textContent===cached.selected) o.classList.add('selected');
          });
        }
      }
    }
    if(cached.result){
      showTrainResult(cached.result);
      document.getElementById('trainSubmitBtn').disabled = true;
    } else {
      document.getElementById('trainSubmitBtn').disabled = false;
    }
  }
}

function trainSelectOpt(el, opt, isMulti) {
  if(isMulti){
    el.classList.toggle('selected');
    window.trainSelected = [];
    el.parentElement.querySelectorAll('.option.selected').forEach(o=>{
      window.trainSelected.push(o.querySelector('.letter').textContent);
    });
  } else {
    el.parentElement.querySelectorAll('.option').forEach(o=>o.classList.remove('selected'));
    el.classList.add('selected');
    window.trainSelected = opt;
  }
}

function submitTrain() {
  if(!currentTrainQ) return;
  const btn = document.getElementById('trainSubmitBtn');
  if(btn) btn.disabled = true;
  const selected = Array.isArray(window.trainSelected)?window.trainSelected.join(','):window.trainSelected;
  if(!selected) { if(btn) btn.disabled = false; return; }
  fetch('/exam/api/train/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_id:currentTrainQ.id,selected})})
    .then(r=>r.json()).then(res=>{
      if(res.code!==0) return;
      showTrainResult(res.data);
      // 缓存结果
      if(trainCache[trainPage]){
        trainCache[trainPage].selected = window.trainSelected;
        trainCache[trainPage].result = res.data;
      }
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

function prevTrain() {
  if(trainPage <= 1) return;
  trainPage--;
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
@app.get("/exam/")
def exam_page():
    return HTMLResponse(content=EXAM_HTML)


@app.get("/api/health")
def health():
    return {"status": "ok"}