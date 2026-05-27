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

<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>铁路校招模拟面试</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 50%, #0d1b3e 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #fff;
    padding: 20px;
}
.phone-container {
    max-width: 420px;
    width: 100%;
    text-align: center;
}
.header {
    margin-bottom: 40px;
}
.header h1 {
    font-size: 22px;
    font-weight: 600;
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
}
.header .sub {
    font-size: 14px;
    color: rgba(255,255,255,0.5);
    letter-spacing: 2px;
}
/* 状态圆圈 */
.status-ring {
    width: 160px;
    height: 160px;
    border-radius: 50%;
    margin: 0 auto 30px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    transition: all 0.5s ease;
}
.status-ring.idle {
    border: 3px solid rgba(255,255,255,0.15);
}
.status-ring.listening {
    border: 3px solid #22c55e;
    box-shadow: 0 0 40px rgba(34,197,94,0.3);
    animation: pulse-green 1.5s ease-in-out infinite;
}
.status-ring.speaking {
    border: 3px solid #8b5cf6;
    box-shadow: 0 0 40px rgba(139,92,246,0.3);
    animation: pulse-purple 1.5s ease-in-out infinite;
}
.status-ring.thinking {
    border: 3px solid #f59e0b;
    box-shadow: 0 0 40px rgba(245,158,11,0.2);
}
@keyframes pulse-green {
    0%,100% { box-shadow: 0 0 30px rgba(34,197,94,0.2); }
    50% { box-shadow: 0 0 60px rgba(34,197,94,0.4); }
}
@keyframes pulse-purple {
    0%,100% { box-shadow: 0 0 30px rgba(139,92,246,0.2); }
    50% { box-shadow: 0 0 60px rgba(139,92,246,0.4); }
}
.status-icon {
    font-size: 48px;
    line-height: 1;
}
.status-text {
    font-size: 15px;
    color: rgba(255,255,255,0.7);
    margin-bottom: 20px;
    min-height: 24px;
}
.progress-dots {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin-bottom: 30px;
}
.dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: rgba(255,255,255,0.15);
    transition: all 0.3s;
}
.dot.done { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.5); }
.dot.active { background: #8b5cf6; box-shadow: 0 0 8px rgba(139,92,246,0.5); }
/* 对话记录 - 简洁 */
.chat-log {
    max-height: 200px;
    overflow-y: auto;
    text-align: left;
    margin-top: 10px;
    padding: 0 10px;
}
.chat-log::-webkit-scrollbar { width: 3px; }
.chat-log::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
.chat-item {
    padding: 8px 12px;
    margin-bottom: 6px;
    border-radius: 12px;
    font-size: 13px;
    line-height: 1.5;
    opacity: 0.8;
}
.chat-item.q { background: rgba(139,92,246,0.15); color: #c4b5fd; }
.chat-item.a { background: rgba(34,197,94,0.1); color: #86efac; }
/* 结束报告 */
.report {
    display: none;
    background: rgba(255,255,255,0.05);
    border-radius: 20px;
    padding: 24px;
    margin-top: 20px;
    text-align: left;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1);
    max-height: 70vh;
    overflow-y: auto;
}
.report h2 {
    font-size: 18px;
    margin-bottom: 16px;
    text-align: center;
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.report .q-item {
    margin-bottom: 16px;
    padding: 12px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
}
.report .q-item h3 {
    font-size: 14px;
    color: #93c5fd;
    margin-bottom: 6px;
}
.report .q-item .label { font-size: 12px; color: rgba(255,255,255,0.4); margin-top: 4px; }
.report .q-item .val { font-size: 13px; color: rgba(255,255,255,0.85); }
.report .q-item .better { color: #fbbf24; }
.restart-btn {
    display: none;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    border: none;
    color: white;
    padding: 12px 40px;
    border-radius: 100px;
    font-size: 15px;
    cursor: pointer;
    margin: 20px auto 0;
}
.restart-btn:hover { transform: scale(1.02); }
/* 按住说话按钮 */
.hold-talk-btn {
    margin: 20px auto 0;
    display: none;
}
.hold-inner {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    margin: 0 auto;
    transition: all 0.2s;
    user-select: none;
    -webkit-user-select: none;
    touch-action: manipulation;
}
.hold-inner:active, .hold-inner.recording {
    transform: scale(1.15);
    background: linear-gradient(135deg, #ef4444, #f97316);
    box-shadow: 0 0 30px rgba(239,68,68,0.4);
}
.hold-icon { font-size: 28px; line-height: 1; }
.hold-label { font-size: 12px; color: rgba(255,255,255,0.9); margin-top: 4px; }
</style>
</head>
<body>
<div class="phone-container">
    <div class="header">
        <h1>🚂 铁路校招模拟面试</h1>
        <div class="sub">AI 面试官 · 全程语音</div>
    </div>

    <div class="status-ring idle" id="statusRing">
        <div class="status-icon" id="statusIcon">🎧</div>
    </div>
    <div class="status-text" id="statusText">准备中...</div>

    <div class="progress-dots" id="progressDots">
        <div class="dot" data-idx="0"></div>
        <div class="dot" data-idx="1"></div>
        <div class="dot" data-idx="2"></div>
        <div class="dot" data-idx="3"></div>
        <div class="dot" data-idx="4"></div>
        <div class="dot" data-idx="5"></div>
    </div>

    <div class="chat-log" id="chatLog"></div>

    <!-- 按住说话按钮（后备方案 - 不自动录音时显示） -->
    <div class="hold-talk-btn" id="holdTalkBtn" style="display:none">
        <div class="hold-inner" id="holdInner">
            <span class="hold-icon" id="holdIcon">🎤</span>
            <span class="hold-label" id="holdLabel">按住说话</span>
        </div>
    </div>

    <div class="report" id="report"></div>
    <button class="restart-btn" id="restartBtn" onclick="location.reload()">🔄 重新面试</button>
</div>

<script>
const sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2,6);
let recognition = null;
let mediaRecorder = null;
let audioChunks = [];
let isProcessing = false;
let finished = false;
let currentQuestionIdx = -1;
let allAnswers = [];
let silenceTimer = null;
let lastSpeechTime = 0;
let useAutoMode = false; // true=auto speech recog, false=hold-to-talk

// DOM
const statusRing = document.getElementById('statusRing');
const statusIcon = document.getElementById('statusIcon');
const statusText = document.getElementById('statusText');
const progressDots = document.getElementById('progressDots');
const chatLog = document.getElementById('chatLog');
const report = document.getElementById('report');
const restartBtn = document.getElementById('restartBtn');
const holdTalkBtn = document.getElementById('holdTalkBtn');
const holdInner = document.getElementById('holdInner');
const holdIcon = document.getElementById('holdIcon');
const holdLabel = document.getElementById('holdLabel');

function setStatus(mode, text, icon) {
    statusRing.className = 'status-ring ' + mode;
    statusText.textContent = text;
    if (icon) statusIcon.textContent = icon;
}

function updateProgress(idx) {
    const dots = progressDots.querySelectorAll('.dot');
    dots.forEach((d, i) => {
        d.className = 'dot';
        if (i < idx) d.classList.add('done');
        else if (i === idx) d.classList.add('active');
    });
}

function addLog(type, text) {
    const div = document.createElement('div');
    div.className = 'chat-item ' + type;
    div.textContent = text.length > 80 ? text.substring(0, 80) + '...' : text;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// ====== Auto Speech Recognition (Chrome) ======
function startAutoListening() {
    if (isProcessing || finished) return;
    if (!useAutoMode) return;
    
    try {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            useAutoMode = false;
            switchToHoldTalk();
            return;
        }
        
        recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = true;
        recognition.interimResults = false;
        
        let finalText = '';
        let hasSpeech = false;
        
        recognition.onresult = function(event) {
            lastSpeechTime = Date.now();
            hasSpeech = true;
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalText += event.results[i][0].transcript;
                }
            }
            
            if (silenceTimer) clearTimeout(silenceTimer);
            silenceTimer = setTimeout(function() {
                if (finalText.trim().length > 0 && !isProcessing) {
                    submitAnswer(finalText.trim());
                }
            }, 800);
        };
        
        recognition.onerror = function(event) {
            if (event.error === 'no-speech') {
                stopAutoListening();
                setTimeout(startAutoListening, 500);
                return;
            }
            if (event.error === 'not-allowed') {
                useAutoMode = false;
                switchToHoldTalk();
                return;
            }
        };
        
        recognition.onend = function() {
            if (hasSpeech && finalText.trim().length > 0 && !isProcessing) {
                submitAnswer(finalText.trim());
            } else if (!isProcessing && !finished && useAutoMode) {
                setTimeout(startAutoListening, 300);
            }
        };
        
        recognition.start();
        setStatus('listening', '🎤 请回答', '🎤');
    } catch(e) {
        useAutoMode = false;
        switchToHoldTalk();
    }
}

function stopAutoListening() {
    if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
    if (recognition) {
        try { recognition.stop(); } catch(e) {}
        recognition = null;
    }
}

// ====== Hold-to-Talk (Fallback for all browsers) ======
function switchToHoldTalk() {
    holdTalkBtn.style.display = 'block';
    setStatus('idle', '按住🎤按钮说话，说完松手', '🎧');
    
    // Setup hold-to-talk
    holdInner.addEventListener('mousedown', startHoldRecord);
    holdInner.addEventListener('mouseup', stopHoldRecord);
    holdInner.addEventListener('mouseleave', stopHoldRecord);
    holdInner.addEventListener('touchstart', function(e) { e.preventDefault(); startHoldRecord(); });
    holdInner.addEventListener('touchend', function(e) { e.preventDefault(); stopHoldRecord(); });
}

async function startHoldRecord() {
    if (isProcessing || finished) return;
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = function(e) {
            audioChunks.push(e.data);
        };
        
        mediaRecorder.onstop = async function() {
            // Stop all tracks
            stream.getTracks().forEach(function(t) { t.stop(); });
            
            if (audioChunks.length === 0) return;
            
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            if (blob.size < 1000) return; // too short
            
            setStatus('thinking', '⏳ 识别语音中...', '⏳');
            
            // Send to backend ASR
            const formData = new FormData();
            formData.append('audio', blob, 'recording.webm');
            
            try {
                const resp = await fetch('api/interview/asr', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();
                
                if (data.code === 0 && data.data.text.trim()) {
                    submitAnswer(data.data.text.trim());
                } else {
                    setStatus('idle', '⚠️ 未识别到语音，重试', '⚠️');
                }
            } catch(e) {
                setStatus('idle', '⚠️ 识别失败，重试', '⚠️');
            }
        };
        
        holdIcon.textContent = '🔴';
        holdLabel.textContent = '松手发送';
        holdInner.classList.add('recording');
        mediaRecorder.start();
    } catch(e) {
        setStatus('idle', '⚠️ 麦克风权限被拒绝', '⚠️');
    }
}

function stopHoldRecord() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        holdIcon.textContent = '🎤';
        holdLabel.textContent = '按住说话';
        holdInner.classList.remove('recording');
    }
}

// === Submit Answer ===
async function submitAnswer(text) {
    if (isProcessing) return;
    isProcessing = true;
    if (useAutoMode) stopAutoListening();
    
    allAnswers.push(text);
    addLog('a', '你的回答：' + text);
    setStatus('thinking', '⏳ AI正在评估...', '⏳');
    
    try {
        const resp = await fetch('api/interview/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'session_id=' + encodeURIComponent(sessionId) + '&message=' + encodeURIComponent(text)
        });
        const data = await resp.json();
        
        if (data.code === 0) {
            const content = data.data.content;
            
            if (data.data.finished) {
                finished = true;
                showFinalReport(content);
                return;
            }
            
            // Parse 下一题
            const nextMatch = content.match(/【下一题】([\s\S]*?)$/);
            const questionText = nextMatch ? nextMatch[1].trim() : '';
            
            if (questionText) {
                currentQuestionIdx++;
                updateProgress(currentQuestionIdx);
                addLog('q', '第' + (currentQuestionIdx+1) + '题：' + questionText);
                
                // Immediately speak the next question
                setStatus('speaking', '🔊 AI正在提问...', '🔊');
                await playTTS(questionText);
                
                // Start listening
                isProcessing = false;
                var nextFn = useAutoMode ? startAutoListening : function(){};
                setTimeout(nextFn, 300);
            } else {
                isProcessing = false;
                var nextFn2 = useAutoMode ? startAutoListening : function(){};
                setTimeout(nextFn2, 500);
            }
        } else {
            setStatus('idle', '⚠️ 处理出错，重试中...', '⚠️');
            isProcessing = false;
            var retryFn = useAutoMode ? startAutoListening : function(){};
            setTimeout(retryFn, 1000);
        }
    } catch(e) {
        setStatus('idle', '⚠️ 网络错误，重试中...', '⚠️');
        isProcessing = false;
        var retryFn2 = useAutoMode ? startAutoListening : function(){};
        setTimeout(retryFn2, 1000);
    }
}

// === TTS ===
function playTTS(text) {
    return new Promise(function(resolve) {
        const ttsText = text.length > 500 ? text.substring(0, 500) + '...' : text;
        fetch('api/interview/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'message=' + encodeURIComponent(ttsText)
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.code === 0 && data.data.audio_url) {
                const audio = new Audio(data.data.audio_url);
                audio.onended = resolve;
                audio.play().catch(resolve);
            } else {
                resolve();
            }
        }).catch(function() { resolve(); });
    });
}

// === Start Interview ===
async function startInterview() {
    setStatus('thinking', '⏳ 面试准备中...', '⏳');
    
    // Detect if browser supports SpeechRecognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    useAutoMode = !!SpeechRecognition;
    
    try {
        const resp = await fetch('api/interview/start?session_id=' + encodeURIComponent(sessionId));
        const data = await resp.json();
        
        if (data.code === 0) {
            currentQuestionIdx = 0;
            updateProgress(0);
            
            const content = data.data.content;
            addLog('q', '第1题：' + content);
            
            setStatus('speaking', '🔊 AI正在提问...', '🔊');
            await playTTS(content);
            
            isProcessing = false;
            if (useAutoMode) {
                setTimeout(startAutoListening, 300);
            } else {
                switchToHoldTalk();
            }
        }
    } catch(e) {
        setStatus('idle', '⚠️ 连接失败，刷新重试', '⚠️');
    }
}

// === Final Report ===
function showFinalReport(content) {
    stopAutoListening();
    setStatus('idle', '✅ 面试已结束', '✅');
    
    report.style.display = 'block';
    restartBtn.style.display = 'block';
    
    // Parse and display nicely
    let html = '<h2>📋 面试总结报告</h2>';
    
    // Format the content
    const lines = content.split('\n');
    let inSection = false;
    
    html += '<div style="white-space:pre-wrap;font-size:13px;line-height:1.7;color:rgba(255,255,255,0.85)">';
    for (let line of lines) {
        line = line.trim();
        if (!line) continue;
        
        if (line.startsWith('第') && line.includes('题')) {
            html += '<div class="q-item"><h3>' + line + '</h3>';
            inSection = true;
        } else if (line === '综合建议' || line.startsWith('总体评价')) {
            if (inSection) { html += '</div>'; inSection = false; }
            html += '<div style="margin:16px 0 8px;font-size:14px;color:#a78bfa;font-weight:600">' + line + '</div>';
        } else if (line.startsWith('可以更好')) {
            html += '<div class="label">可以更好：</div><div class="val better">' + line.replace('可以更好：', '') + '</div>';
        } else if (line.startsWith('评分')) {
            html += '<div class="label">' + line + '</div>';
        } else if (line.startsWith('你的回答')) {
            html += '<div class="label">' + line + '</div>';
        } else if (line.startsWith('评价')) {
            html += '<div class="val">' + line + '</div>';
        } else {
            html += '<div>' + line + '</div>';
        }
    }
    if (inSection) html += '</div>';
    html += '</div>';
    
    report.innerHTML = html;
}

// Auto start on page load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(startInterview, 500);
});
</script>
</body>
</html>
"""