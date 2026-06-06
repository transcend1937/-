"""
轻量访客统计模块
使用 JSON 文件存储，支持按日/按页查询
"""
import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict

DATA_FILE = os.path.join(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"), "assets", "analytics.json")
MAX_RECORDS = 20000  # 最多保留2万条记录


def _load():
    """加载统计数据"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save(records):
    """保存统计数据"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    # 超出上限则清理最旧的记录
    if len(records) > MAX_RECORDS:
        records = records[-MAX_RECORDS:]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def record(page: str, referrer: str = "", title: str = ""):
    """记录一次访问"""
    records = _load()
    records.append({
        "t": int(time.time()),
        "p": page,
        "r": referrer[:200] if referrer else "",
        "title": title[:100] if title else "",
        "ua": "",  # 从请求头获取
    })
    _save(records)


def record_from_request(page: str, request_headers: dict, title: str = ""):
    """从请求记录访问"""
    records = _load()
    records.append({
        "t": int(time.time()),
        "p": page,
        "r": request_headers.get("referer", "")[:200],
        "title": title[:100] if title else "",
        "ua": request_headers.get("user-agent", "")[:200],
    })
    _save(records)


def get_stats(days: int = 7):
    """获取统计摘要"""
    records = _load()
    now = time.time()
    cutoff = now - days * 86400

    # 过滤时间范围
    recent = [r for r in records if r["t"] >= cutoff]

    # 按日统计
    daily = defaultdict(int)
    # 按页统计
    pages = defaultdict(int)
    # 按小时统计
    hourly = defaultdict(int)

    for r in recent:
        day = datetime.fromtimestamp(r["t"]).strftime("%m-%d")
        daily[day] += 1
        pages[r["p"]] += 1
        h = datetime.fromtimestamp(r["t"]).hour
        hourly[f"{h:02d}:00"] += 1

    return {
        "total": len(recent),
        "total_all": len(records),
        "days": days,
        "daily": dict(sorted(daily.items())),
        "pages": dict(sorted(pages.items(), key=lambda x: -x[1])),
        "hourly": dict(sorted(hourly.items())),
        "latest": sorted(recent, key=lambda x: -x["t"])[:50],
    }