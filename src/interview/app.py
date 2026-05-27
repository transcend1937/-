"""铁路院校模拟面试 - Web 应用"""

import os
import json
import uuid
import logging
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from langchain_core.messages import HumanMessage, AIMessage

from agents.agent import build_agent, get_better_answers

logger = logging.getLogger(__name__)

app = FastAPI(title="铁路院校模拟面试")

# ============== 会话管理 ==============
# 内存会话存储，每个会话对应一个独立的 agent + thread_id
_sessions: dict[str, dict] = {}

def _get_or_create_session(session_id: str) -> dict:
    """获取或创建面试会话"""
    if session_id not in _sessions:
        agent = build_agent()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        _sessions[session_id] = {
            "agent": agent,
            "config": config,
            "history": [],
            "started": False,
            "finished": False,
        }
    return _sessions[session_id]


# ============== API 路由 ==============

@app.get("/api/interview/start")
def start_interview(session_id: str = "default"):
    """开始新的面试，返回AI面试官的开场问候"""
    session = _get_or_create_session(session_id)
    session["started"] = True
    session["finished"] = False

    agent = session["agent"]
    config = session["config"]

    # 发送开场消息
    response = agent.invoke(
        {"messages": [HumanMessage(content="你好，我准备好了，请开始面试吧。")]},
        config=config
    )

    ai_msg = response["messages"][-1]
    content = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    session["history"] = [{"role": "ai", "content": content}]
    return {"code": 0, "data": {"role": "ai", "content": content}}


@app.post("/api/interview/chat")
def interview_chat(session_id: str = Form("default"), message: str = Form("")):
    """发送面试者回答，返回AI面试官的评价和下一题"""
    if not message or not message.strip():
        return {"code": 1, "message": "回答不能为空"}

    session = _get_or_create_session(session_id)
    if not session.get("started"):
        # 自动开始面试
        start_interview(session_id)
        session = _get_or_create_session(session_id)

    agent = session["agent"]
    config = session["config"]

    # 发送用户消息
    response = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )

    ai_msg = response["messages"][-1]
    content = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    session["history"].append({"role": "user", "content": message})
    session["history"].append({"role": "ai", "content": content})

    # 检测面试是否结束
    if "面试总结" in content or "评估报告" in content or "面试到此结束" in content:
        session["finished"] = True

    return {
        "code": 0,
        "data": {
            "role": "ai",
            "content": content,
            "finished": session["finished"]
        }
    }


@app.get("/api/interview/status")
def get_status(session_id: str = "default"):
    """获取面试状态"""
    session = _sessions.get(session_id)
    if not session:
        return {"code": 0, "data": {"started": False, "finished": False, "history": [], "better_answers": []}}
    return {
        "code": 0,
        "data": {
            "started": session.get("started", False),
            "finished": session.get("finished", False),
            "history": session.get("history", []),
            "better_answers": get_better_answers()
        }
    }


@app.get("/api/interview/better-answers")
def get_collected_answers():
    """获取所有收录的优秀回答"""
    return {"code": 0, "data": get_better_answers()}


@app.get("/api/interview/reset")
def reset_interview(session_id: str = "default"):
    """重置面试会话"""
    if session_id in _sessions:
        del _sessions[session_id]
    # 清空之前存储的优秀回答
    from agents.agent import get_better_answers
    return {"code": 0, "message": "面试已重置"}


# ============== 前端 SPA ==============

@app.get("/")
@app.get("/interview")
@app.get("/interview/")
async def interview_page():
    """返回面试模拟 SPA 页面"""
    return HTMLResponse(SPA_HTML)

SPA_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>铁路院校模拟面试</title>
<style>
:root {
    --primary: #1a3a5c;
    --primary-light: #2c5f8a;
    --primary-dark: #0f2440;
    --accent: #e8a838;
    --accent-light: #f5c46a;
    --bg: #f0f4f8;
    --card-bg: #ffffff;
    --text: #1a2332;
    --text-muted: #6b7a8f;
    --border: #dce3ed;
    --success: #2ecc71;
    --warning: #f39c12;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(26,58,92,0.08);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}
.header {
    background: linear-gradient(135deg, var(--primary-dark), var(--primary));
    color: white;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    position: sticky;
    top: 0;
    z-index: 100;
}
.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.header-icon {
    width: 36px;
    height: 36px;
    background: var(--accent);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}
.header h1 {
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.header-sub {
    font-size: 12px;
    opacity: 0.8;
    margin-top: 2px;
}
.header-actions { display: flex; gap: 8px; }
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}
.btn-primary {
    background: var(--accent);
    color: var(--primary-dark);
}
.btn-primary:hover { background: var(--accent-light); transform: translateY(-1px); }
.btn-outline {
    background: transparent;
    color: white;
    border: 1.5px solid rgba(255,255,255,0.3);
}
.btn-outline:hover { border-color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.1); }
.btn-sm { padding: 6px 12px; font-size: 12px; }

.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px 16px;
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 20px;
    min-height: calc(100vh - 72px);
}

/* 侧边栏 */
.sidebar {
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 16px;
    box-shadow: var(--shadow);
    height: fit-content;
    position: sticky;
    top: 92px;
}
.sidebar-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--border);
}
.question-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.q-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 13px;
    cursor: default;
    transition: all 0.2s;
    border: 1.5px solid transparent;
}
.q-item.pending {
    background: #f8fafc;
    color: var(--text-muted);
}
.q-item.active {
    background: #eef4fb;
    border-color: var(--primary-light);
    color: var(--primary);
    font-weight: 600;
}
.q-item.done {
    background: #eafaf1;
    border-color: var(--success);
    color: #1a7a3a;
}
.q-badge {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    flex-shrink: 0;
}
.q-item.pending .q-badge { background: #e8ecf0; color: #8a9aa8; }
.q-item.active .q-badge { background: var(--primary); color: white; }
.q-item.done .q-badge { background: var(--success); color: white; }
.q-label { flex: 1; line-height: 1.3; }
.q-status-icon { font-size: 14px; }

/* 主聊天区 */
.chat-area {
    display: flex;
    flex-direction: column;
    background: var(--card-bg);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
    min-height: 500px;
}
.chat-header {
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
    background: #fafbfd;
}
.chat-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}
.chat-header-info h3 { font-size: 14px; font-weight: 600; }
.chat-header-info p { font-size: 12px; color: var(--text-muted); }
.chat-header-progress {
    margin-left: auto;
    font-size: 13px;
    color: var(--text-muted);
    background: #f0f4f8;
    padding: 4px 12px;
    border-radius: 20px;
}

.chat-messages {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    max-height: 550px;
    min-height: 400px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.message {
    display: flex;
    gap: 10px;
    max-width: 85%;
    animation: fadeIn 0.3s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.message.ai { align-self: flex-start; }
.message.user { align-self: flex-end; flex-direction: row-reverse; }
.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
}
.message.ai .message-avatar { background: var(--primary); color: white; }
.message.user .message-avatar { background: var(--accent); color: var(--primary-dark); }
.message-bubble {
    padding: 12px 16px;
    border-radius: 12px;
    line-height: 1.6;
    font-size: 14px;
    white-space: pre-wrap;
    word-wrap: break-word;
}
.message.ai .message-bubble {
    background: #f0f4f8;
    border-bottom-left-radius: 4px;
}
.message.user .message-bubble {
    background: var(--primary);
    color: white;
    border-bottom-right-radius: 4px;
}
.message-bubble h3, .message-bubble h4 {
    margin: 8px 0 4px;
    font-size: 14px;
}
.message-bubble strong { font-weight: 600; }
.message-bubble hr {
    margin: 8px 0;
    border: none;
    border-top: 1px solid var(--border);
}
.message-bubble ul, .message-bubble ol {
    padding-left: 20px;
    margin: 4px 0;
}
.message-bubble p { margin: 4px 0; }
.message.user .message-bubble hr { border-color: rgba(255,255,255,0.2); }

/* 输入区 */
.chat-input {
    padding: 16px 20px;
    border-top: 1px solid var(--border);
    background: #fafbfd;
}
.chat-input textarea {
    width: 100%;
    min-height: 60px;
    max-height: 150px;
    padding: 12px 16px;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
}
.chat-input textarea:focus { border-color: var(--primary-light); }
.chat-input-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
}
.chat-input-info { font-size: 12px; color: var(--text-muted); }
.btn-send {
    padding: 10px 28px;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
}
.btn-send:hover { background: var(--primary-light); transform: translateY(-1px); }
.btn-send:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

/* 加载动画 */
.loading-dots {
    display: inline-flex;
    gap: 4px;
    align-items: center;
    padding: 4px 0;
}
.loading-dots span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-muted);
    animation: bounce 1.4s infinite ease-in-out both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%,80%,100% { transform: scale(0); } 40% { transform: scale(1); } }

/* 空状态 */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-muted);
    text-align: center;
    gap: 12px;
    min-height: 350px;
}
.empty-icon { font-size: 48px; opacity: 0.5; }
.empty-title { font-size: 18px; font-weight: 600; color: var(--text); }
.empty-desc { font-size: 14px; max-width: 320px; line-height: 1.6; }

/* 完成状态 */
.finish-banner {
    background: linear-gradient(135deg, #eafaf1, #d5f5e3);
    border: 1.5px solid var(--success);
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 8px;
    text-align: center;
}
.finish-banner h3 { color: #1a7a3a; margin-bottom: 4px; }
.finish-banner p { font-size: 13px; color: #2d8a4a; }

/* Toast 提示 */
.toast {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--primary-dark);
    color: white;
    padding: 12px 24px;
    border-radius: 10px;
    font-size: 14px;
    opacity: 0;
    transition: all 0.3s;
    z-index: 999;
    pointer-events: none;
}
.toast.show { opacity: 1; bottom: 32px; }

/* 响应式 */
@media (max-width: 768px) {
    .container { grid-template-columns: 1fr; padding: 12px; }
    .sidebar { position: static; }
    .header { padding: 12px 16px; }
    .header h1 { font-size: 15px; }
    .message { max-width: 95%; }
    .chat-header-progress { font-size: 11px; padding: 2px 8px; }
}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <div class="header-icon">🚂</div>
        <div>
            <h1>铁路院校模拟面试</h1>
            <div class="header-sub">AI 面试官 · 6 道经典面试题</div>
        </div>
    </div>
    <div class="header-actions">
        <button class="btn btn-outline btn-sm" onclick="resetInterview()">🔄 重新开始</button>
    </div>
</div>

<div class="container">
    <!-- 侧边栏 -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-title">📋 面试进度</div>
        <div class="question-list" id="questionList"></div>
    </div>

    <!-- 聊天区 -->
    <div class="chat-area">
        <div class="chat-header">
            <div class="chat-avatar">🎓</div>
            <div class="chat-header-info">
                <h3>AI 面试官</h3>
                <p id="statusText">点击下方按钮开始面试</p>
            </div>
            <div class="chat-header-progress" id="progressBadge">0 / 6</div>
        </div>

        <div class="chat-messages" id="chatMessages">
            <div class="empty-state" id="emptyState">
                <div class="empty-icon">🎯</div>
                <div class="empty-title">准备好面试了吗？</div>
                <div class="empty-desc">
                    这是一场铁路岗位模拟面试，共 6 道题。<br>
                    AI 面试官会逐题提问，并对你的回答进行评价和建议。
                </div>
                <button class="btn btn-primary" onclick="startInterview()" style="margin-top:8px;padding:12px 32px;font-size:15px;">
                    🚀 开始面试
                </button>
            </div>
        </div>

        <div class="chat-input" id="chatInput" style="display:none;">
            <textarea id="answerInput" placeholder="输入你的回答..." rows="2"
                onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendAnswer();}"></textarea>
            <div class="chat-input-actions">
                <span class="chat-input-info">💡 按 Enter 发送 · Shift+Enter 换行</span>
                <button class="btn-send" id="sendBtn" onclick="sendAnswer()">
                    ✨ 发送回答
                </button>
            </div>
        </div>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
const QUESTION_LABELS = ['服从调剂', '偏远分配', '独生子女', '为什么选铁路', '接受夜班', '为什么报我局'];
let isWaiting = false;
let interviewStarted = false;
let interviewFinished = false;

function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}

function renderQuestions(currentIdx) {
    const list = document.getElementById('questionList');
    let html = '';
    for (let i = 0; i < 6; i++) {
        let status = 'pending';
        let icon = '';
        if (i < currentIdx) { status = 'done'; icon = '✅'; }
        else if (i === currentIdx) { status = 'active'; icon = '▶'; }
        else { icon = '' + (i + 1); }
        html += '<div class="q-item ' + status + '">' +
            '<div class="q-badge">' + (status === 'done' ? '✓' : (status === 'active' ? '●' : (i + 1))) + '</div>' +
            '<div class="q-label">' + QUESTION_LABELS[i] + '</div>' +
            (status === 'done' ? '<span class="q-status-icon">✅</span>' : '') +
        '</div>';
    }
    list.innerHTML = html;
    document.getElementById('progressBadge').textContent = currentIdx + ' / 6';
}

function addMessage(role, content) {
    const container = document.getElementById('chatMessages');
    const emptyState = document.getElementById('emptyState');
    if (emptyState) emptyState.style.display = 'none';

    // 移除loading
    const loadingMsg = document.querySelector('.message.loading');
    if (loadingMsg) loadingMsg.remove();

    const div = document.createElement('div');
    div.className = 'message ' + role;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'ai' ? '🎓' : '👤';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatContent(content);

    div.appendChild(avatar);
    div.appendChild(bubble);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function formatContent(content) {
    return content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/### (.*?)(\n|$)/g, '<h3>$1</h3>\n')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[评分\]:?/gi, '<strong>📊 评分</strong>')
        .replace(/\n---/g, '<hr>')
        .replace(/\n- /g, '\n• ')
        .replace(/\n/g, '<br>');
}

function showLoading() {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message ai loading';
    div.innerHTML = '<div class="message-avatar">🎓</div><div class="message-bubble"><div class="loading-dots"><span></span><span></span><span></span></div></div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function updateStatus(text) {
    document.getElementById('statusText').textContent = text;
}

async function startInterview() {
    if (isWaiting) return;
    isWaiting = true;
    interviewStarted = true;

    document.getElementById('chatInput').style.display = 'block';
    document.getElementById('sendBtn').disabled = true;
    showLoading();
    updateStatus('面试官正在准备...');

    try {
        const res = await fetch('/api/interview/start?session_id=default');
        const data = await res.json();
        if (data.code === 0) {
            addMessage('ai', data.data.content);
            renderQuestions(1);
            updateStatus('问题 1/6 - 等待你的回答');
        }
    } catch (e) {
        showToast('网络错误，请重试');
    }

    isWaiting = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('answerInput').focus();
}

async function sendAnswer() {
    const input = document.getElementById('answerInput');
    const text = input.value.trim();
    if (!text || isWaiting) return;

    input.value = '';
    isWaiting = true;
    document.getElementById('sendBtn').disabled = true;

    addMessage('user', text);
    showLoading();
    updateStatus('面试官正在评价...');

    try {
        const res = await fetch('/api/interview/chat?session_id=default', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'message=' + encodeURIComponent(text)
        });
        const data = await res.json();
        if (data.code === 0) {
            addMessage('ai', data.data.content);

            if (data.data.finished) {
                interviewFinished = true;
                document.getElementById('chatInput').style.display = 'none';
                updateStatus('✅ 面试已结束');
                renderQuestions(6);

                // 显示完成横幅
                const container = document.getElementById('chatMessages');
                const banner = document.createElement('div');
                banner.className = 'finish-banner';
                banner.innerHTML = '<h3>🎉 面试已全部完成！</h3><p>点击"重新开始"可再次进行模拟面试</p>';
                container.appendChild(banner);
                container.scrollTop = container.scrollHeight;
                showToast('🎉 面试完成！');
            } else {
                // 计算当前进度 - 根据已回答的用户消息数推断
                const answeredCount = document.querySelectorAll('.message.user').length;
                renderQuestions(answeredCount + 1);
                updateStatus('等待你的回答');
                document.getElementById('answerInput').focus();
            }
        }
    } catch (e) {
        showToast('网络错误，请重试');
    }

    isWaiting = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('answerInput').focus();
}

async function resetInterview() {
    if (isWaiting) return;
    try {
        await fetch('/api/interview/reset?session_id=default');
    } catch(e) {}

    interviewStarted = false;
    interviewFinished = false;
    document.getElementById('chatMessages').innerHTML = `
        <div class="empty-state" id="emptyState">
            <div class="empty-icon">🎯</div>
            <div class="empty-title">准备好面试了吗？</div>
            <div class="empty-desc">
                这是一场铁路岗位模拟面试，共 6 道题。<br>
                AI 面试官会逐题提问，并对你的回答进行评价和建议。
            </div>
            <button class="btn btn-primary" onclick="startInterview()" style="margin-top:8px;padding:12px 32px;font-size:15px;">
                🚀 开始面试
            </button>
        </div>`;
    document.getElementById('chatInput').style.display = 'none';
    renderQuestions(0);
    updateStatus('点击下方按钮开始面试');
    document.getElementById('sendBtn').disabled = false;
    isWaiting = false;
    showToast('已重置面试');
}

// 初始化
renderQuestions(0);
</script>
</body>
</html>"""