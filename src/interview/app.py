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
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>铁路校招模拟面试</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(160deg, #fce4ec 0%, #f3e5f5 40%, #e8eaf6 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #1a1a2e;
    padding: 20px;
    overflow: hidden;
}
.phone-container {
    max-width: 400px;
    width: 100%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
}
/* 顶部标题 */
.top-bar {
    position: absolute;
    top: 16px;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 10px;
}
.top-bar .title {
    font-size: 16px;
    font-weight: 600;
    color: #5c4d7a;
}
.btn-caption {
    background: rgba(255,255,255,0.7);
    border: none;
    color: #5c4d7a;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    cursor: pointer;
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    gap: 4px;
}
.btn-caption.active { background: #7c5cbf; color: #fff; }
/* 头像圆圈 */
.avatar-ring {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e8d5f5, #c9b8e8);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    position: relative;
    transition: all 0.3s;
    border: 3px solid rgba(255,255,255,0.8);
    box-shadow: 0 8px 32px rgba(90,60,140,0.15);
}
.avatar-ring.listening {
    border-color: #7c5cbf;
    box-shadow: 0 0 40px rgba(124,92,191,0.25);
}
.avatar-ring.speaking {
    border-color: #e8a0bf;
    box-shadow: 0 0 40px rgba(232,160,191,0.3);
}
.avatar-ring.thinking {
    border-color: #f5c842;
    box-shadow: 0 0 40px rgba(245,200,66,0.2);
}
.avatar-icon {
    font-size: 52px;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1));
}
/* 状态文字 */
.status-area {
    text-align: center;
    margin-bottom: 30px;
}
.status-dots {
    display: flex;
    gap: 6px;
    justify-content: center;
    margin-bottom: 8px;
    height: 16px;
}
.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #c9b8e8;
    transition: all 0.3s;
}
.status-dot.active {
    background: #7c5cbf;
    animation: dot-bounce 0.8s ease-in-out infinite;
}
.status-dot.active:nth-child(2) { animation-delay: 0.15s; }
.status-dot.active:nth-child(3) { animation-delay: 0.3s; }
@keyframes dot-bounce {
    0%,100% { transform: translateY(0); opacity: 0.4; }
    50% { transform: translateY(-4px); opacity: 1; }
}
.status-label {
    font-size: 15px;
    color: #8a7aaa;
    min-height: 22px;
}
/* 进度条 */
.progress-bar {
    display: flex;
    gap: 6px;
    justify-content: center;
    margin-bottom: 20px;
    width: 80%;
}
.progress-seg {
    flex: 1;
    height: 4px;
    border-radius: 4px;
    background: rgba(200,180,220,0.4);
    transition: all 0.3s;
}
.progress-seg.done { background: #7c5cbf; }
.progress-seg.active { background: #7c5cbf; opacity: 0.6; }
/* 字幕（可选） */
.subtitle-area {
    display: none;
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 12px 16px;
    margin: 0 20px 16px;
    max-height: 100px;
    overflow-y: auto;
    width: 100%;
    text-align: center;
    font-size: 14px;
    color: #5c4d7a;
    line-height: 1.5;
    border: 1px solid rgba(200,180,220,0.3);
}
.subtitle-area.show { display: block; }
.subtitle-area .sub-label {
    font-size: 11px;
    color: #b0a0c8;
    margin-bottom: 4px;
}
/* 底部按钮 */
.bottom-bar {
    position: absolute;
    bottom: 40px;
    left: 0;
    right: 0;
    display: flex;
    justify-content: center;
    gap: 30px;
    padding: 0 30px;
}
.bottom-btn {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 22px;
}
.bottom-btn:active { transform: scale(0.9); }
.btn-end {
    background: #ff6b6b;
    color: white;
    box-shadow: 0 4px 16px rgba(255,107,107,0.3);
}
.btn-end:hover { transform: scale(1.05); }
/* 报告覆盖层 */
.report-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    backdrop-filter: blur(8px);
    z-index: 100;
    padding: 30px 20px;
    overflow-y: auto;
}
.report-card {
    background: linear-gradient(160deg, #fce4ec, #f3e5f5);
    border-radius: 24px;
    padding: 24px;
    max-width: 400px;
    margin: 40px auto;
    box-shadow: 0 8px 40px rgba(0,0,0,0.15);
}
.report-card h2 {
    font-size: 20px;
    text-align: center;
    color: #5c4d7a;
    margin-bottom: 16px;
}
.report-item {
    margin-bottom: 14px;
    padding: 12px;
    background: rgba(255,255,255,0.6);
    border-radius: 14px;
}
.report-item h3 { font-size: 13px; color: #7c5cbf; margin-bottom: 4px; }
.report-item .rl { font-size: 11px; color: #b0a0c8; margin-top: 3px; }
.report-item .rv { font-size: 13px; color: #3a2a5a; }
.report-item .better { color: #e07b3a; font-weight: 500; }
.report-restart {
    display: block;
    margin: 20px auto 0;
    background: linear-gradient(135deg, #7c5cbf, #b08ad8);
    border: none;
    color: white;
    padding: 12px 36px;
    border-radius: 100px;
    font-size: 15px;
    cursor: pointer;
}
</style>
</head>
<body>
<div class="phone-container">
    <!-- 顶部 -->
    <div class="top-bar">
        <span class="title">🚂 铁路校招模拟面试</span>
        <button class="btn-caption" id="captionBtn" onclick="toggleCaption()">💬 字幕</button>
    </div>

    <!-- 头像 -->
    <div class="avatar-ring listening" id="avatarRing">
        <div class="avatar-icon" id="avatarIcon">👩‍💼</div>
    </div>

    <!-- 状态 -->
    <div class="status-area">
        <div class="status-dots" id="statusDots">
            <span class="status-dot active"></span>
            <span class="status-dot active"></span>
            <span class="status-dot active"></span>
        </div>
        <div class="status-label" id="statusLabel">准备中...</div>
    </div>

    <!-- 进度 -->
    <div class="progress-bar" id="progressBar">
        <div class="progress-seg" data-idx="0"></div>
        <div class="progress-seg" data-idx="1"></div>
        <div class="progress-seg" data-idx="2"></div>
        <div class="progress-seg" data-idx="3"></div>
        <div class="progress-seg" data-idx="4"></div>
        <div class="progress-seg" data-idx="5"></div>
    </div>

    <!-- 字幕 -->
    <div class="subtitle-area" id="subtitleArea">
        <div class="sub-label">实时字幕</div>
        <div id="subtitleText">-</div>
    </div>

    <!-- 底部 -->
    <div class="bottom-bar">
        <button class="bottom-btn btn-end" id="endBtn" onclick="endCall()">📞</button>
    </div>
</div>

<!-- 报告覆盖层 -->
<div class="report-overlay" id="reportOverlay">
    <div class="report-card" id="reportCard"></div>
</div>

<script>
'use strict';
const sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2,6);
let isProcessing = false;
let finished = false;
let currentIdx = -1;
let allAnswers = [];
let mediaRecorder = null;
let audioCtx = null;
let analyser = null;
let audioStream = null;
let audioChunks = [];
let isRecording = false;
let silenceStart = 0;
let hasSpoken = false;
let captionOn = false;

// DOM
const avatarRing = document.getElementById('avatarRing');
const avatarIcon = document.getElementById('avatarIcon');
const statusLabel = document.getElementById('statusLabel');
const statusDots = document.querySelectorAll('.status-dot');
const subtitleText = document.getElementById('subtitleText');
const subtitleArea = document.getElementById('subtitleArea');
const progressBar = document.getElementById('progressBar');
const reportOverlay = document.getElementById('reportOverlay');
const reportCard = document.getElementById('reportCard');

function setStatus(mode, label, icon) {
    avatarRing.className = 'avatar-ring ' + mode;
    statusLabel.textContent = label;
    if (icon) avatarIcon.textContent = icon;
    // Dots animation
    statusDots.forEach(function(d) {
        d.classList.toggle('active', mode === 'listening');
    });
}

function updateProgress(idx) {
    var segs = progressBar.querySelectorAll('.progress-seg');
    segs.forEach(function(s, i) {
        s.className = 'progress-seg';
        if (i < idx) s.classList.add('done');
        else if (i === idx) s.classList.add('active');
    });
}

function showSubtitle(text) {
    if (captionOn) {
        subtitleText.textContent = text || '-';
    }
}

function toggleCaption() {
    captionOn = !captionOn;
    document.getElementById('captionBtn').classList.toggle('active', captionOn);
    subtitleArea.classList.toggle('show', captionOn);
}

// ====== Voice Detection via AudioContext ======
const SILENCE_THRESHOLD = 0.02;  // RMS threshold
const SILENCE_TIMEOUT = 600;    // ms of silence before submit (缩短到0.6秒)

async function startContinuousRecording() {
    try {
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        var source = audioCtx.createMediaStreamSource(audioStream);
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);

        audioChunks = [];
        isRecording = true;
        hasSpoken = false;
        silenceStart = 0;

        // Start MediaRecorder
        mediaRecorder = new MediaRecorder(audioStream);
        mediaRecorder.ondataavailable = function(e) {
            audioChunks.push(e.data);
        };
        mediaRecorder.onstop = function() {
            // Handle in submitRecording
        };
        mediaRecorder.start(200);

        setStatus('listening', '正在听...', '👩‍💼');

        // Start voice activity detection loop
        detectVoice();
    } catch(e) {
        setStatus('thinking', '⚠️ 麦克风权限被拒绝，请允许后刷新', '❌');
    }
}

function detectVoice() {
    if (!isRecording || !analyser) return;

    var data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(data);

    // Calculate RMS
    var sum = 0;
    for (var i = 0; i < data.length; i++) {
        var val = (data[i] - 128) / 128;
        sum += val * val;
    }
    var rms = Math.sqrt(sum / data.length);

    if (rms > SILENCE_THRESHOLD) {
        // Voice detected
        hasSpoken = true;
        silenceStart = 0;
    } else if (hasSpoken) {
        // Silence detected after speech
        var now = Date.now();
        if (silenceStart === 0) {
            silenceStart = now;
        } else if (now - silenceStart > SILENCE_TIMEOUT) {
            // Silence for too long, submit
            submitRecording();
            return;
        }
    }

    if (isRecording) {
        requestAnimationFrame(detectVoice);
    }
}

async function submitRecording() {
    if (!isRecording || !hasSpoken) {
        // No speech detected, restart
        stopRecording();
        setTimeout(startContinuousRecording, 200);
        return;
    }

    isRecording = false;
    stopRecording();

    if (audioChunks.length === 0) {
        setTimeout(startContinuousRecording, 200);
        return;
    }

    var blob = new Blob(audioChunks, { type: 'audio/webm' });
    if (blob.size < 2000) {
        // Too short, restart
        setTimeout(startContinuousRecording, 300);
        return;
    }

    setStatus('thinking', '识别中...', '🤔');

    var formData = new FormData();
    formData.append('audio', blob, 'recording.webm');

    try {
        var resp = await fetch('api/interview/asr', { method: 'POST', body: formData });
        var data = await resp.json();

        if (data.code === 0 && data.data.text.trim()) {
            var transcript = data.data.text.trim();
            showSubtitle('你说：' + transcript);
            await submitAnswer(transcript);
        } else {
            setStatus('listening', '请再说一遍', '👩‍💼');
            setTimeout(startContinuousRecording, 200);
        }
    } catch(e) {
        setStatus('listening', '重试中...', '👩‍💼');
        setTimeout(startContinuousRecording, 300);
    }
}

function stopRecording() {
    isRecording = false;
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        try { mediaRecorder.stop(); } catch(e) {}
    }
    if (audioStream) {
        audioStream.getTracks().forEach(function(t) { t.stop(); });
        audioStream = null;
    }
    if (audioCtx) {
        audioCtx.close().catch(function(){});
        audioCtx = null;
    }
    analyser = null;
}

// ====== Submit Answer ======
async function submitAnswer(text) {
    if (isProcessing) return;
    isProcessing = true;

    allAnswers.push(text);
    setStatus('thinking', '思考中...', '🤔');
    showSubtitle('AI评估中...');

    try {
        var resp = await fetch('api/interview/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'session_id=' + encodeURIComponent(sessionId) + '&message=' + encodeURIComponent(text)
        });
        var data = await resp.json();

        if (data.code === 0) {
            var content = data.data.content;

            if (data.data.finished) {
                finished = true;
                showFinalReport(content);
                return;
            }

            // Parse 【下一题】
            var nextMatch = content.match(/【下一题】([\s\S]*?)$/);
            var questionText = nextMatch ? nextMatch[1].trim() : '';

            if (questionText) {
                currentIdx++;
                updateProgress(currentIdx);
                showSubtitle('第' + (currentIdx+1) + '题：' + questionText);

                setStatus('speaking', '正在提问...', '👩‍💼');
                await playTTS(questionText);

                isProcessing = false;
                setTimeout(startContinuousRecording, 200);
            } else {
                isProcessing = false;
                setTimeout(startContinuousRecording, 200);
            }
        } else {
            setStatus('listening', '出错了，请重试', '👩‍💼');
            isProcessing = false;
            setTimeout(startContinuousRecording, 300);
        }
    } catch(e) {
        setStatus('listening', '网络错误，重试', '👩‍💼');
        isProcessing = false;
        setTimeout(startContinuousRecording, 300);
    }
}

// ====== TTS ======
function playTTS(text) {
    return new Promise(function(resolve) {
        var ttsText = text.length > 500 ? text.substring(0, 500) + '...' : text;
        fetch('api/interview/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'message=' + encodeURIComponent(ttsText)
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.code === 0 && data.data.audio_url) {
                var audio = new Audio(data.data.audio_url);
                audio.onended = resolve;
                audio.play().catch(resolve);
            } else {
                resolve();
            }
        }).catch(function() { resolve(); });
    });
}

// ====== Start ======
async function startInterview() {
    setStatus('thinking', '准备中...', '🤔');

    try {
        var resp = await fetch('api/interview/start?session_id=' + encodeURIComponent(sessionId));
        var data = await resp.json();

        if (data.code === 0) {
            currentIdx = 0;
            updateProgress(0);

            var content = data.data.content;
            showSubtitle('第1题：' + content);

            setStatus('speaking', '正在提问...', '👩‍💼');
            await playTTS(content);

            isProcessing = false;
            setTimeout(startContinuousRecording, 200);
        }
    } catch(e) {
        setStatus('thinking', '连接失败，刷新重试', '❌');
    }
}

// ====== End Call ======
function endCall() {
    stopRecording();
    isProcessing = true;
    setStatus('thinking', '已挂断', '📞');
    if (!finished) {
        // Show partial report
        setTimeout(function() {
            location.reload();
        }, 500);
    }
}

// ====== Final Report ======
function showFinalReport(content) {
    stopRecording();
    setStatus('thinking', '面试结束', '✅');

    var html = '<h2>📋 面试总结报告</h2>';
    var lines = content.split('\n');
    var inSection = false;

    html += '<div style="white-space:pre-wrap;font-size:13px;line-height:1.7;color:#3a2a5a">';
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (!line) continue;

        if (line.startsWith('第') && line.includes('题')) {
            html += '<div class="report-item"><h3>' + line + '</h3>';
            inSection = true;
        } else if (line === '综合建议' || line.startsWith('总体评价')) {
            if (inSection) { html += '</div>'; inSection = false; }
            html += '<div style="margin:14px 0 6px;font-size:14px;color:#7c5cbf;font-weight:600">' + line + '</div>';
        } else if (line.startsWith('可以更好')) {
            html += '<div class="rl">可以更好：</div><div class="rv better">' + line.replace('可以更好：', '') + '</div>';
        } else if (line.startsWith('评分')) {
            html += '<div class="rl">' + line + '</div>';
        } else if (line.startsWith('你的回答')) {
            html += '<div class="rl">' + line + '</div>';
        } else if (line.startsWith('评价')) {
            html += '<div class="rv" style="margin-top:2px">' + line + '</div>';
        } else {
            html += '<div>' + line + '</div>';
        }
    }
    if (inSection) html += '</div>';
    html += '</div>';
    html += '<button class="report-restart" onclick="location.reload()">🔄 重新面试</button>';

    reportCard.innerHTML = html;
    reportOverlay.style.display = 'block';
}

// Auto start
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(startInterview, 600);
});
</script>
</body>
</html>
"""