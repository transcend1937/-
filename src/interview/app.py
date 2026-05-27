"""铁路校招模拟面试 - Web 应用（语音交互版）"""

import os
import json
import uuid
import base64
import logging
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from langchain_core.messages import HumanMessage, AIMessage

from agents.agent import build_agent, get_better_answers
from coze_coding_dev_sdk import ASRClient, TTSClient

logger = logging.getLogger(__name__)

app = FastAPI(title="铁路校招模拟面试")

# ============== 会话管理 ==============
_sessions: dict[str, dict] = {}

def _get_or_create_session(session_id: str) -> dict:
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


# ============== ASR / TTS ==============

@app.post("/api/interview/asr")
async def speech_to_text(audio: UploadFile = File(...)):
    """语音识别：接收录音文件，返回识别后的文字"""
    try:
        audio_bytes = await audio.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        asr = ASRClient()
        text, _ = asr.recognize(base64_data=audio_b64)

        return {"code": 0, "data": {"text": text}}
    except Exception as e:
        logger.error(f"ASR error: {e}")
        return {"code": 1, "message": f"语音识别失败: {str(e)}"}


@app.post("/api/interview/tts")
async def text_to_speech(message: str = Form(...)):
    """语音合成：返回AI回复的音频URL"""
    try:
        tts = TTSClient()
        audio_url, audio_size = tts.synthesize(
            uid="interview_user",
            text=message,
            speaker="zh_female_xiaohe_uranus_bigtts",
            audio_format="mp3",
            sample_rate=24000,
            speech_rate=0,
        )
        return {"code": 0, "data": {"audio_url": audio_url, "audio_size": audio_size}}
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return {"code": 1, "message": f"语音合成失败: {str(e)}"}


# ============== API 路由 ==============

@app.get("/api/interview/start")
def start_interview(session_id: str = "default"):
    """开始新的面试，返回AI面试官的开场问候"""
    session = _get_or_create_session(session_id)
    session["started"] = True
    session["finished"] = False

    agent = session["agent"]
    config = session["config"]

    response = agent.invoke(
        {"messages": [HumanMessage(content="你好，我准备好了，请开始面试吧。")]},
        config=config
    )

    ai_msg = response["messages"][-1]
    content = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    session["history"] = [{"role": "ai", "content": content}]
    return {"code": 0, "data": {"role": "ai", "content": content}}


@app.post("/api/interview/chat")
def send_answer(session_id: str = Form("default"), message: str = Form("")):
    """用户发送回答，AI面试官回复评价+下一题"""
    session = _get_or_create_session(session_id)
    if not session.get("started"):
        return {"code": 1, "message": "面试尚未开始，请先调用 /start"}

    agent = session["agent"]
    config = session["config"]

    response = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )

    ai_msg = response["messages"][-1]
    content = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    session["history"].append({"role": "user", "content": message})
    session["history"].append({"role": "ai", "content": content})

    finished = "面试总结" in content or "评估报告" in content or "全部完成" in content
    if finished:
        session["finished"] = True

    return {"code": 0, "data": {"role": "ai", "content": content, "finished": session["finished"]}}


@app.get("/api/interview/better-answers")
def get_collected_answers():
    """获取所有收录的优秀回答"""
    return {"code": 0, "data": get_better_answers()}


@app.get("/api/interview/reset")
def reset_interview(session_id: str = "default"):
    """重置面试会话"""
    if session_id in _sessions:
        del _sessions[session_id]
    return {"code": 0, "message": "面试已重置"}


# ============== 前端 SPA ==============

@app.get("/")
async def interview_page():
    return HTMLResponse(SPA_HTML)

SPA_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>铁路校招模拟面试</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

/* ===== 顶部通话状态 ===== */
.call-header {
    background: linear-gradient(135deg, #1a237e, #0d47a1);
    padding: 24px 20px 20px;
    text-align: center;
    flex-shrink: 0;
}
.call-header h1 {
    font-size: 20px;
    font-weight: 600;
    color: white;
    margin-bottom: 4px;
}
.call-header .subtitle {
    font-size: 13px;
    color: rgba(255,255,255,0.7);
}

/* ===== 状态指示器 ===== */
.status-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 20px 20px;
    flex-shrink: 0;
}
.status-ring {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    transition: all 0.3s;
    margin-bottom: 12px;
}
.status-ring.idle { background: #1e293b; border: 2px solid #334155; }
.status-ring.listening {
    background: #065f46;
    border: 2px solid #34d399;
    box-shadow: 0 0 30px rgba(52,211,153,0.3);
    animation: pulse 1.5s ease-in-out infinite;
}
.status-ring.speaking {
    background: #1e3a5f;
    border: 2px solid #60a5fa;
    box-shadow: 0 0 20px rgba(96,165,250,0.3);
}
.status-ring.thinking {
    background: #5b21b6;
    border: 2px solid #a78bfa;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 20px rgba(52,211,153,0.2); }
    50% { box-shadow: 0 0 40px rgba(52,211,153,0.5); }
}

.status-text {
    font-size: 15px;
    color: #94a3b8;
    text-align: center;
}

/* ===== 实时语音转写 ===== */
.transcript-area {
    padding: 8px 20px 12px;
    text-align: center;
    min-height: 60px;
    flex-shrink: 0;
}
.transcript-text {
    font-size: 18px;
    color: #f1f5f9;
    line-height: 1.5;
    transition: all 0.1s;
}
.transcript-text.interim { color: #94a3b8; font-style: italic; }
.transcript-text:empty::before {
    content: '等待语音...';
    color: #475569;
}

/* ===== 对话记录 ===== */
.chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 12px 16px;
    scroll-behavior: smooth;
}
.chat-area::-webkit-scrollbar { width: 4px; }
.chat-area::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }

.msg {
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 8px;
    max-width: 92%;
    font-size: 14px;
    line-height: 1.6;
    animation: fadeIn 0.3s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.msg.user {
    background: #1e293b;
    color: #e2e8f0;
    margin-left: auto;
    border-bottom-right-radius: 4px;
}
.msg.ai {
    background: #1a237e;
    color: #e8eaf6;
    margin-right: auto;
    border-bottom-left-radius: 4px;
}
.msg .label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 4px;
}
.msg .content { white-space: pre-wrap; word-break: break-word; }

/* ===== 底部操作区 ===== */
.bottom-bar {
    padding: 12px 20px 24px;
    text-align: center;
    flex-shrink: 0;
}
.call-btn {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
    padding: 14px 48px;
    border-radius: 100px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
.call-btn:hover { transform: scale(1.03); box-shadow: 0 4px 20px rgba(37,99,235,0.4); }
.call-btn.secondary {
    background: #1e293b;
    color: #94a3b8;
}
.call-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
</style>
</head>
<body>

<div class="call-header">
    <h1>🚂 铁路校招模拟面试</h1>
    <div class="subtitle">全程语音 · AI 面试官</div>
</div>

<div class="status-area">
    <div class="status-ring idle" id="statusRing">🎙</div>
    <div class="status-text" id="statusText">加载中...</div>
</div>

<div class="transcript-area">
    <div class="transcript-text" id="transcriptText"></div>
</div>

<div class="chat-area" id="chatArea"></div>

<div class="bottom-bar">
    <button class="call-btn" id="callBtn" onclick="toggleCall()">📞 开始面试</button>
</div>

<script>
// ============== 全局状态 ==============
let sessionId = 'call_' + Date.now();
let recognition = null;
let silenceTimer = null;
let collectedText = '';
let isProcessing = false;
let isAiSpeaking = false;
let finished = false;
let nextQuestionText = '';
let isCallActive = false;

const statusRing = document.getElementById('statusRing');
const statusText = document.getElementById('statusText');
const transcriptText = document.getElementById('transcriptText');
const chatArea = document.getElementById('chatArea');
const callBtn = document.getElementById('callBtn');

// ============== UI 更新 ==============
function setStatus(mode, text) {
    statusRing.className = 'status-ring ' + mode;
    statusText.textContent = text;
}

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    const label = role === 'user' ? '🧑 你' : '🤖 面试官';
    div.innerHTML = '<div class="label">' + label + '</div><div class="content">' + escapeHtml(content) + '</div>';
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function showTranscript(text, isInterim) {
    transcriptText.textContent = text || '';
    transcriptText.className = 'transcript-text' + (isInterim ? ' interim' : '');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============== SpeechRecognition ==============
function initRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        setStatus('idle', '⚠️ 浏览器不支持语音识别，请使用Chrome');
        return false;
    }
    recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'zh-CN';
    
    recognition.onresult = function(e) {
        let interim = '';
        let final = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) {
                final += e.results[i][0].transcript;
            } else {
                interim += e.results[i][0].transcript;
            }
        }
        if (final) {
            collectedText += final;
            showTranscript(collectedText + interim, true);
            resetSilenceTimer();
        } else {
            showTranscript(collectedText + (interim ? '...' + interim : ''), true);
        }
    };
    
    recognition.onerror = function(e) {
        console.log('Recognition error:', e.error);
        if (e.error === 'no-speech') return;
        if (e.error === 'aborted') return;
        setStatus('idle', '⚠️ 语音识别出错，点击重试');
        setTimeout(tryRestartRecognition, 1000);
    };
    
    recognition.onend = function() {
        if (isProcessing || isAiSpeaking || !isCallActive) return;
        // If we have collected text, process it
        if (collectedText.trim()) {
            submitAnswer(collectedText.trim());
            collectedText = '';
        }
        // Restart recognition
        tryRestartRecognition();
    };
    
    return true;
}

function tryRestartRecognition() {
    if (isProcessing || isAiSpeaking || !isCallActive || finished) return;
    try {
        if (recognition) recognition.start();
    } catch(e) {}
}

function startRecognition() {
    if (!recognition) initRecognition();
    if (!recognition) return;
    try {
        recognition.start();
        setStatus('listening', '🎤 请回答...');
    } catch(e) {}
}

function stopRecognition() {
    try { if (recognition) recognition.stop(); } catch(e) {}
}

function resetSilenceTimer() {
    if (silenceTimer) clearTimeout(silenceTimer);
    silenceTimer = setTimeout(function() {
        if (collectedText.trim()) {
            stopRecognition();
            const text = collectedText.trim();
            collectedText = '';
            showTranscript('');
            submitAnswer(text);
        }
    }, 1500);
}

// ============== TTS 语音播报 ==============
async function playTTS(text, onEnd) {
    isAiSpeaking = true;
    setStatus('speaking', '🔊 AI正在说话...');
    stopRecognition();
    
    try {
        const ttsText = text.length > 500 ? text.substring(0, 500) + '...' : text;
        const resp = await fetch('api/interview/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'message=' + encodeURIComponent(ttsText)
        });
        const data = await resp.json();
        if (data.code === 0 && data.data.audio_url) {
            const audio = new Audio(data.data.audio_url);
            audio.onended = function() {
                isAiSpeaking = false;
                if (onEnd) onEnd();
            };
            audio.play().catch(function() {
                isAiSpeaking = false;
                if (onEnd) onEnd();
            });
        } else {
            isAiSpeaking = false;
            if (onEnd) onEnd();
        }
    } catch(e) {
        isAiSpeaking = false;
        if (onEnd) onEnd();
    }
}

// ============== API 交互 ==============
async function submitAnswer(text) {
    if (isProcessing) return;
    isProcessing = true;
    setStatus('thinking', '⏳ 面试官正在思考...');
    
    addMessage('user', text);
    
    try {
        const resp = await fetch('api/interview/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'session_id=' + encodeURIComponent(sessionId) + '&message=' + encodeURIComponent(text)
        });
        const data = await resp.json();
        
        if (data.code === 0) {
            const respContent = data.data.content;
            finished = data.data.finished;
            
            // 解析评估和下一题
            const nextMatch = respContent.match(/【下一题】([\s\S]*?)$/);
            nextQuestionText = nextMatch ? nextMatch[1].trim() : '';
            
            addMessage('ai', respContent);
            
            if (finished) {
                setStatus('idle', '🎉 面试全部完成！');
                callBtn.textContent = '🔄 重新面试';
                callBtn.disabled = false;
                isProcessing = false;
                return;
            }
            
            // 自动播报下一题
            if (nextQuestionText) {
                await playTTS(nextQuestionText, function() {
                    isProcessing = false;
                    collectedText = '';
                    showTranscript('');
                    setStatus('listening', '🎤 请回答...');
                    startRecognition();
                });
            } else {
                isProcessing = false;
                startRecognition();
            }
        } else {
            setStatus('idle', '❌ 处理失败，请重试');
            isProcessing = false;
        }
    } catch(e) {
        setStatus('idle', '❌ 网络错误，请重试');
        isProcessing = false;
    }
}

async function startInterview() {
    callBtn.disabled = true;
    callBtn.textContent = '⏳ 准备中...';
    setStatus('thinking', '⏳ 正在连接面试官...');
    
    try {
        const resp = await fetch('api/interview/start?session_id=' + encodeURIComponent(sessionId));
        const data = await resp.json();
        
        if (data.code === 0) {
            const msg = data.data.content;
            addMessage('ai', msg);
            
            // 解析第一题
            const nextMatch = msg.match(/【下一题】([\s\S]*?)$/) || msg.match(/请问[^。]*。/);
            const firstQ = nextMatch ? nextMatch[1] || nextMatch[0] : msg;
            
            await playTTS(firstQ, function() {
                setStatus('listening', '🎤 请回答...');
                if (initRecognition()) {
                    startRecognition();
                }
            });
        } else {
            setStatus('idle', '❌ 连接失败');
            callBtn.disabled = false;
            callBtn.textContent = '📞 重新开始';
        }
    } catch(e) {
        setStatus('idle', '❌ 网络错误');
        callBtn.disabled = false;
        callBtn.textContent = '📞 重新开始';
    }
}

// ============== 呼叫控制 ==============
function toggleCall() {
    if (!isCallActive) {
        isCallActive = true;
        callBtn.textContent = '📞 通话中...';
        callBtn.disabled = true;
        chatArea.innerHTML = '';
        finishMatch = null;
        collectedText = '';
        nextQuestionText = '';
        finished = false;
        // Reset session
        fetch('api/interview/reset?session_id=' + encodeURIComponent(sessionId));
        setTimeout(startInterview, 300);
    } else {
        // Hang up
        isCallActive = false;
        stopRecognition();
        if (silenceTimer) clearTimeout(silenceTimer);
        setStatus('idle', '📴 通话已结束');
        callBtn.textContent = '📞 重新面试';
        callBtn.disabled = false;
    }
}
</script>
</body>
</html>"""