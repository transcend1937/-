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
.call-header {
    background: linear-gradient(135deg, #1a237e, #0d47a1);
    padding: 24px 20px 18px;
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
.status-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 20px 16px;
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
    animation: pulse-green 1.5s ease-in-out infinite;
}
.status-ring.speaking {
    background: #1e3a5f;
    border: 2px solid #60a5fa;
    box-shadow: 0 0 20px rgba(96,165,250,0.3);
    animation: pulse-blue 1.5s ease-in-out infinite;
}
.status-ring.thinking {
    background: #5b21b6;
    border: 2px solid #a78bfa;
    animation: pulse-purple 1s ease-in-out infinite;
}
@keyframes pulse-green {
    0%,100% { box-shadow: 0 0 20px rgba(52,211,153,0.2); }
    50% { box-shadow: 0 0 40px rgba(52,211,153,0.5); }
}
@keyframes pulse-blue {
    0%,100% { box-shadow: 0 0 15px rgba(96,165,250,0.2); }
    50% { box-shadow: 0 0 35px rgba(96,165,250,0.5); }
}
@keyframes pulse-purple {
    0%,100% { box-shadow: 0 0 15px rgba(167,139,250,0.2); }
    50% { box-shadow: 0 0 35px rgba(167,139,250,0.5); }
}
.status-text {
    font-size: 15px;
    color: #94a3b8;
    text-align: center;
    min-height: 24px;
}
.transcript-area {
    padding: 4px 20px 8px;
    text-align: center;
    min-height: 40px;
    flex-shrink: 0;
}
.transcript-text {
    font-size: 17px;
    color: #f1f5f9;
    line-height: 1.5;
}
.transcript-text.interim { color: #94a3b8; font-style: italic; }
.transcript-text:empty::before {
    content: '🎤 正在听...';
    color: #34d399;
}
.chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 8px 16px;
    scroll-behavior: smooth;
}
.chat-area::-webkit-scrollbar { width: 3px; }
.chat-area::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
.chat-msg {
    margin-bottom: 10px;
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 13px;
    line-height: 1.5;
    max-width: 90%;
}
.chat-msg.ai {
    background: rgba(59,130,246,0.1);
    border-left: 3px solid #3b82f6;
    margin-right: auto;
}
.chat-msg.user {
    background: rgba(52,211,153,0.08);
    border-left: 3px solid #34d399;
    margin-left: auto;
}
.chat-msg .sender { font-size: 11px; color: #64748b; margin-bottom: 2px; }
.chat-msg .text { color: #e2e8f0; }
.chat-msg .label-score { font-size: 11px; color: #fbbf24; margin-top: 3px; }
.chat-msg .label-better { font-size: 11px; color: #60a5fa; margin-top: 2px; }
.chat-msg .label-next { font-size: 11px; color: #a78bfa; margin-top: 2px; }
.progress-bar {
    display: flex;
    gap: 8px;
    justify-content: center;
    padding: 8px 20px;
    flex-shrink: 0;
}
.pdot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #334155;
    transition: all 0.3s;
}
.pdot.done { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }
.pdot.active { background: #818cf8; box-shadow: 0 0 8px rgba(129,140,248,0.6); }
.bottom-bar {
    padding: 12px 20px;
    text-align: center;
    flex-shrink: 0;
    background: rgba(15,23,42,0.8);
}
.call-btn {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    border: none;
    color: white;
    padding: 10px 32px;
    border-radius: 100px;
    font-size: 15px;
    cursor: pointer;
    transition: all 0.2s;
}
.call-btn:hover { transform: scale(1.03); }
.report-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.7);
    z-index: 100;
    justify-content: center;
    align-items: center;
    padding: 20px;
}
.report-box {
    background: #1e293b;
    border-radius: 20px;
    padding: 24px;
    max-width: 420px;
    width: 100%;
    max-height: 80vh;
    overflow-y: auto;
    border: 1px solid #334155;
}
.report-box h2 { font-size: 18px; margin-bottom: 16px; text-align: center; color: #60a5fa; }
.report-box .qi { margin-bottom: 14px; padding: 10px; background: #0f172a; border-radius: 10px; }
.report-box .qi h3 { font-size: 13px; color: #93c5fd; margin-bottom: 4px; }
.report-box .qi .l { font-size: 11px; color: #64748b; margin-top: 3px; }
.report-box .qi .v { font-size: 12px; color: #e2e8f0; }
.report-box .qi .better { color: #fbbf24; }
.restart-btn {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border: none; color: white; padding: 10px 32px;
    border-radius: 100px; font-size: 14px; cursor: pointer;
    margin-top: 16px; width: 100%;
}
</style>
</head>
<body>

<div class="call-header">
    <h1>🚂 铁路校招模拟面试</h1>
    <div class="subtitle">全程语音 · AI 面试官</div>
</div>

<div class="progress-bar" id="progressBar">
    <div class="pdot" data-idx="0"></div>
    <div class="pdot" data-idx="1"></div>
    <div class="pdot" data-idx="2"></div>
    <div class="pdot" data-idx="3"></div>
    <div class="pdot" data-idx="4"></div>
    <div class="pdot" data-idx="5"></div>
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
    <button class="call-btn" id="endBtn" onclick="endCall()" style="display:none;">🔴 结束面试</button>
</div>

<div class="report-overlay" id="reportOverlay">
    <div class="report-box" id="reportBox"></div>
</div>

<script>
let sessionId = 'call_' + Date.now() + '_' + Math.random().toString(36).substr(2,4);
let mediaRecorder = null;
let audioCtx = null;
let analyser = null;
let stream = null;
let isRecording = false;
let isProcessing = false;
let isAiSpeaking = false;
let finished = false;
let currentQIdx = -1;
const SILENCE_THRESHOLD = 0.008;
const SILENCE_TIMEOUT_MS = 300;
let audioChunks = [];
let silenceStart = null;
let lastActivity = 0;

const statusRing = document.getElementById('statusRing');
const statusText = document.getElementById('statusText');
const transcriptText = document.getElementById('transcriptText');
const chatArea = document.getElementById('chatArea');
const progressBar = document.getElementById('progressBar');
const endBtn = document.getElementById('endBtn');
const reportOverlay = document.getElementById('reportOverlay');

function setStatus(mode, text, icon) {
    statusRing.className = 'status-ring ' + mode;
    statusText.textContent = text || '';
    if (icon) statusRing.textContent = icon;
}

function updateProgress(idx) {
    const dots = progressBar.querySelectorAll('.pdot');
    dots.forEach(function(d, i) {
        d.className = 'pdot';
        if (i < idx) d.classList.add('done');
        else if (i === idx) d.classList.add('active');
    });
}

function addMsg(role, text) {
    const div = document.createElement('div');
    div.className = 'chat-msg ' + role;
    const label = role === 'ai' ? 'AI 面试官' : '你的回答';
    let display = text.length > 100 ? text.substring(0, 100) + '...' : text;
    div.innerHTML = '<div class="sender">' + label + '</div><div class="text">' + display + '</div>';
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function addAIMsg(text) {
    const div = document.createElement('div');
    div.className = 'chat-msg ai';
    let html = '<div class="sender">AI 面试官</div>';
    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const s = lines[i].trim();
        if (!s) continue;
        if (s.startsWith('评分')) html += '<div class="label-score">' + s + '</div>';
        else if (s.startsWith('可以更好') || s.startsWith('改进版')) html += '<div class="label-better">' + s + '</div>';
        else if (s.startsWith('【下一题】')) html += '<div class="label-next">' + s + '</div>';
        else html += '<div class="text">' + s + '</div>';
    }
    div.innerHTML = html;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function startContinuousRecording() {
    if (isRecording || isProcessing || isAiSpeaking || finished) return;
    navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true } })
    .then(function(s) {
        stream = s;
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const src = audioCtx.createMediaStreamSource(stream);
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        src.connect(analyser);
        
        audioChunks = [];
        silenceStart = null;
        lastActivity = Date.now();
        
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorder.ondataavailable = function(e) {
            if (e.data.size > 0) audioChunks.push(e.data);
        };
        mediaRecorder.onstop = function() {
            if (audioChunks.length > 0 && !isProcessing && !finished) {
                sendAudioToASR();
            }
        };
        mediaRecorder.start(100);
        isRecording = true;
        setStatus('listening', '正在听...', '🎤');
        transcriptText.innerHTML = '';
        requestAnimationFrame(detectVoice);
    })
    .catch(function(e) {
        setStatus('idle', '麦克风权限被拒绝', '⚠️');
    });
}

function detectVoice() {
    if (!analyser || !isRecording || isProcessing || isAiSpeaking || finished) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
        const val = (data[i] - 128) / 128;
        sum += val * val;
    }
    const rms = Math.sqrt(sum / data.length);
    if (rms > SILENCE_THRESHOLD) {
        silenceStart = null;
        lastActivity = Date.now();
        transcriptText.className = 'transcript-text';
    } else {
        if (silenceStart === null) silenceStart = Date.now();
        if ((Date.now() - silenceStart) > SILENCE_TIMEOUT_MS && (Date.now() - lastActivity) > 400) {
            stopAndSubmit();
            return;
        }
    }
    requestAnimationFrame(detectVoice);
}

function stopAndSubmit() {
    if (!isRecording) return;
    isRecording = false;
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        try { mediaRecorder.stop(); } catch(e) {}
    }
    cleanupStream();
    setStatus('thinking', '识别中...', '⏳');
}

function cleanupStream() {
    if (audioCtx) { try { audioCtx.close(); } catch(e) {} audioCtx = null; }
    analyser = null;
    if (stream) { stream.getTracks().forEach(function(t){ try { t.stop(); } catch(e) {} }); stream = null; }
}

async function sendAudioToASR() {
    if (audioChunks.length === 0) {
        isProcessing = false;
        setTimeout(startContinuousRecording, 50);
        return;
    }
    const blob = new Blob(audioChunks, { type: 'audio/webm' });
    audioChunks = [];
    if (blob.size < 200) {
        isProcessing = false;
        setTimeout(startContinuousRecording, 50);
        return;
    }
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');
    try {
        const resp = await fetch('api/interview/asr', { method: 'POST', body: formData });
        const data = await resp.json();
        if (data.code === 0 && data.data.text.trim().length > 0) {
            const userText = data.data.text.trim();
            transcriptText.textContent = userText;
            addMsg('user', userText);
            setStatus('thinking', '思考中...', '⏳');
            await submitAnswer(userText);
        } else {
            isProcessing = false;
            setTimeout(startContinuousRecording, 50);
        }
    } catch(e) {
        isProcessing = false;
        setTimeout(startContinuousRecording, 100);
    }
}

async function submitAnswer(text) {
    isProcessing = true;
    try {
        const resp = await fetch('api/interview/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'session_id=' + encodeURIComponent(sessionId) + '&message=' + encodeURIComponent(text)
        });
        const data = await resp.json();
        if (data.code === 0) {
            const content = data.data.content;
            addAIMsg(content);
            if (data.data.finished) {
                finished = true;
                endBtn.style.display = 'none';
                setTimeout(function() { showReport(content); }, 200);
                return;
            }
            const nextMatch = content.match(/【下一题】([\s\S]*?)$/);
            const questionText = nextMatch ? nextMatch[1].trim() : '';
            if (questionText) {
                currentQIdx++;
                updateProgress(currentQIdx);
                setStatus('speaking', 'AI正在提问...', '🔊');
                await playTTS(questionText);
                isProcessing = false;
                isAiSpeaking = false;
                setTimeout(startContinuousRecording, 20);
            } else {
                isProcessing = false;
                setTimeout(startContinuousRecording, 50);
            }
        } else {
            isProcessing = false;
            setTimeout(startContinuousRecording, 100);
        }
    } catch(e) {
        isProcessing = false;
        setTimeout(startContinuousRecording, 100);
    }
}

function playTTS(text) {
    return new Promise(function(resolve) {
        fetch('api/interview/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'message=' + encodeURIComponent(text.length > 500 ? text.substring(0, 500) : text)
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.code === 0 && data.data.audio_url) {
                const audio = new Audio(data.data.audio_url);
                audio.onended = resolve;
                audio.play().catch(resolve);
            } else { resolve(); }
        })
        .catch(function() { resolve(); });
    });
}

async function startInterview() {
    setStatus('thinking', '准备中...', '⏳');
    try {
        const resp = await fetch('api/interview/start?session_id=' + encodeURIComponent(sessionId));
        const data = await resp.json();
        if (data.code === 0) {
            currentQIdx = 0;
            updateProgress(0);
            const content = data.data.content;
            addAIMsg(content);
            const qMatch = content.match(/请回答第一个问题：(.*?)$/);
            const toSpeak = qMatch ? qMatch[1].trim() : content;
            setStatus('speaking', 'AI正在提问...', '🔊');
            await playTTS(toSpeak || content);
            endBtn.style.display = 'inline-block';
            isAiSpeaking = false;
            setTimeout(startContinuousRecording, 20);
        }
    } catch(e) {
        setStatus('idle', '连接失败，刷新重试', '⚠️');
    }
}

function showReport(content) {
    setStatus('idle', '面试结束', '✅');
    transcriptText.innerHTML = '面试已结束';
    let html = '<h2>面试总结报告</h2>';
    const lines = content.split('\n');
    let inQ = false;
    let reportHtml = '';
    for (let i = 0; i < lines.length; i++) {
        const s = lines[i].trim();
        if (!s) continue;
        if (s.startsWith('第') && s.includes('题')) {
            if (inQ) reportHtml += '</div>';
            reportHtml += '<div class="qi"><h3>' + s + '</h3>';
            inQ = true;
        } else if (s === '综合建议' || s.startsWith('总体评价')) {
            if (inQ) { reportHtml += '</div>'; inQ = false; }
            reportHtml += '<div style="margin:14px 0 6px;font-size:14px;color:#a78bfa;font-weight:600">' + s + '</div>';
        } else if (s.startsWith('可以更好')) {
            reportHtml += '<div class="l">可以更好：</div><div class="v better">' + s.replace('可以更好：', '') + '</div>';
        } else if (s.startsWith('评分')) {
            reportHtml += '<div class="l">' + s + '</div>';
        } else if (s.startsWith('你的回答')) {
            reportHtml += '<div class="l">' + s + '</div>';
        } else if (s.startsWith('评价')) {
            reportHtml += '<div class="v">' + s + '</div>';
        } else {
            reportHtml += '<div class="v">' + s + '</div>';
        }
    }
    if (inQ) reportHtml += '</div>';
    html += reportHtml;
    html += '<button class="restart-btn" onclick="location.reload()">重新面试</button>';
    document.getElementById('reportBox').innerHTML = html;
    reportOverlay.style.display = 'flex';
}

function endCall() {
    stopAndSubmit();
    cleanupStream();
    isRecording = false;
    isProcessing = false;
    finished = true;
    endBtn.style.display = 'none';
    setStatus('idle', '面试已结束', '🔴');
    transcriptText.innerHTML = '面试已结束，刷新页面重新开始';
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(startInterview, 200);
});
</script>
</body>
</html>"""
