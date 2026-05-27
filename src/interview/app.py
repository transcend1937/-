"""铁路院校模拟面试 - Web 应用（语音交互版）"""

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

app = FastAPI(title="铁路院校模拟面试")

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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>铁路院校模拟面试</title>
<style>
:root {
    --primary: #1a3a5c;
    --primary-light: #2c5f8a;
    --primary-dark: #0f2440;
    --accent: #e8a838;
    --bg: #f0f4f8;
    --card-bg: #ffffff;
    --text: #1a2332;
    --text-muted: #6b7a8f;
    --success: #2ecc71;
    --warning: #f39c12;
    --shadow: 0 4px 24px rgba(26,58,92,0.1);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}
.header {
    background: linear-gradient(135deg, var(--primary-dark), var(--primary));
    color: white;
    padding: 16px 24px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    flex-shrink: 0;
}
.header h1 { font-size: 20px; font-weight: 600; }
.header p { font-size: 13px; opacity: 0.8; margin-top: 4px; }

.chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 20px 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    scroll-behavior: smooth;
}
.chat-area:empty { justify-content: center; align-items: center; }

.msg {
    max-width: 85%;
    padding: 14px 18px;
    border-radius: 16px;
    line-height: 1.7;
    font-size: 15px;
    animation: fadeIn 0.3s ease;
    word-break: break-word;
    white-space: pre-wrap;
}
.msg.ai {
    align-self: flex-start;
    background: var(--card-bg);
    border: 1px solid #e8edf4;
    border-bottom-left-radius: 4px;
    box-shadow: var(--shadow);
    color: var(--text);
}
.msg.user {
    align-self: flex-end;
    background: var(--primary);
    color: white;
    border-bottom-right-radius: 4px;
}
.msg.ai .label {
    display: inline-block;
    font-size: 12px;
    font-weight: 600;
    color: var(--primary-light);
    margin-bottom: 6px;
}
.msg .sound-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-top: 8px;
    padding: 6px 14px;
    border: none;
    border-radius: 20px;
    background: #eef3f9;
    color: var(--primary);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
}
.msg .sound-btn:hover { background: #dce6f2; }
.msg .sound-btn.playing { background: var(--accent); color: white; }
.sound-btn svg { width: 16px; height: 16px; }

.bottom-bar {
    flex-shrink: 0;
    padding: 16px 24px 24px;
    background: white;
    border-top: 1px solid #e8edf4;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
}
.start-btn {
    padding: 14px 48px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--primary), var(--primary-light));
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 16px rgba(26,58,92,0.25);
}
.start-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(26,58,92,0.3); }
.start-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.mic-btn {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    border: 4px solid var(--primary);
    background: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
    position: relative;
}
.mic-btn:hover { background: #f0f4ff; transform: scale(1.05); }
.mic-btn.recording {
    border-color: #e74c3c;
    background: #fdedec;
    animation: pulse 1.2s infinite;
}
.mic-btn.recording .mic-icon { color: #e74c3c; }
.mic-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
.mic-btn .mic-icon { font-size: 32px; color: var(--primary); }
.mic-btn .recording-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #e74c3c;
    position: absolute;
    top: -4px;
    right: -4px;
    display: none;
}
.mic-btn.recording .recording-dot { display: block; }

.hint-text {
    font-size: 13px;
    color: var(--text-muted);
    text-align: center;
}
.hint-text.recording { color: #e74c3c; font-weight: 600; }

/* 下一题按钮 */
.next-btn-wrapper {
    display: flex;
    justify-content: center;
    width: 100%;
    padding: 4px 0;
}
.next-btn {
    background: var(--primary);
    color: white;
    border: none;
    padding: 12px 36px;
    border-radius: 25px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(41,65,112,0.3);
}
.next-btn:hover {
    background: var(--secondary);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(41,65,112,0.4);
}

.loading-dots::after {
    content: '';
    animation: dots 1.5s infinite;
}
@keyframes dots {
    0% { content: ''; }
    33% { content: '.'; }
    66% { content: '..'; }
    100% { content: '...'; }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(231,76,60,0.4); }
    70% { box-shadow: 0 0 0 16px rgba(231,76,60,0); }
    100% { box-shadow: 0 0 0 0 rgba(231,76,60,0); }
}

.waiting-anim {
    display: flex;
    gap: 6px;
    align-items: center;
    padding: 14px 18px;
    background: var(--card-bg);
    border: 1px solid #e8edf4;
    border-radius: 16px;
    align-self: flex-start;
}
.waiting-anim .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--primary-light);
    animation: bounce 1.4s infinite ease-in-out;
}
.waiting-anim .dot:nth-child(2) { animation-delay: 0.2s; }
.waiting-anim .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40% { transform: scale(1); opacity: 1; }
}

.hidden { display: none !important; }
</style>
</head>
<body>

<div class="header">
    <h1>🚂 铁路院校模拟面试</h1>
    <p>AI 面试官 · 全程语音回答</p>
</div>

<div class="chat-area" id="chatArea">
    <div class="msg ai">
        <div class="label">🎯 AI 面试官</div>
        欢迎参加铁路院校模拟面试！点击下方「开始面试」按钮，AI 面试官将逐题提问，你用语音回答即可。
    </div>
</div>

<div class="bottom-bar" id="bottomBar">
    <button class="start-btn" id="startBtn" onclick="startInterview()">🚀 开始面试</button>
    <div id="voiceControls" class="hidden" style="display:flex;flex-direction:column;align-items:center;gap:8px;width:100%;">
        <button class="mic-btn" id="micBtn" onclick="toggleRecording()">
            <span class="mic-icon">🎤</span>
            <span class="recording-dot"></span>
        </button>
        <div class="hint-text" id="hintText">点击🎤按钮，开始语音回答</div>
    </div>
</div>

<script>
let sessionId = 'default_' + Date.now();
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let isProcessing = false;
let finished = false;
let nextQuestionText = '';

const chatArea = document.getElementById('chatArea');
const startBtn = document.getElementById('startBtn');
const voiceControls = document.getElementById('voiceControls');
const micBtn = document.getElementById('micBtn');
const hintText = document.getElementById('hintText');

// === 开始面试 ===
async function startInterview() {
    startBtn.disabled = true;
    startBtn.textContent = '⏳ 面试准备中...';
    addMessage('ai', '🎯 AI 面试官', '面试即将开始，请准备好...');

    try {
        const resp = await fetch('api/interview/start?session_id=' + encodeURIComponent(sessionId));
        const data = await resp.json();
        if (data.code === 0) {
            const msg = data.data.content;
            addMessage('ai', '🎯 AI 面试官', msg);
            playTTS(msg, function() { enableRecording(); });
        }
        startBtn.classList.add('hidden');
    } catch (e) {
        addMessage('ai', '⚠️ 系统', '连接失败，请检查服务是否正常');
        startBtn.disabled = false;
        startBtn.textContent = '🚀 重新开始';
    }
}

function enableRecording() {
    voiceControls.classList.remove('hidden');
    voiceControls.style.display = 'flex';
    micBtn.disabled = false;
    isProcessing = false;
    hintText.textContent = '🎤 请点击🎤按钮，语音回答';
}

// === 录音 ===
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    if (isProcessing) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ?
                'audio/webm;codecs=opus' : 'audio/webm'
        });

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            // 停止所有音轨
            stream.getTracks().forEach(t => t.stop());

            if (audioChunks.length === 0) return;

            isProcessing = true;
            micBtn.disabled = true;
            hintText.textContent = '🔊 正在识别你的回答...';

            // 合成音频blob
            const audioBlob = new Blob(audioChunks, {
                type: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ?
                    'audio/webm;codecs=opus' : 'audio/webm'
            });

            // 显示录入完成的消息
            addMessage('user', '👤 你', '(语音回答已提交，正在识别...)');

            // 发送ASR
            try {
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.webm');
                const asrResp = await fetch('api/interview/asr', { method: 'POST', body: formData });
                const asrData = await asrResp.json();

                if (asrData.code !== 0) {
                    hintText.textContent = '❌ 语音识别失败，请重试';
                    isProcessing = false;
                    micBtn.disabled = false;
                    return;
                }

                const userText = asrData.data.text;
                if (!userText || userText.trim() === '') {
                    hintText.textContent = '❌ 未识别到语音，请重试';
                    isProcessing = false;
                    micBtn.disabled = false;
                    return;
                }

                // 更新用户消息为识别后的文字
                updateLastUserMessage(userText);

                hintText.textContent = '🤔 AI 面试官正在思考...';

                // 发送到AI面试官
                const chatFormData = new FormData();
                chatFormData.append('session_id', sessionId);
                chatFormData.append('message', userText);
                const chatResp = await fetch('api/interview/chat', { method: 'POST', body: chatFormData });

                const chatData = await chatResp.json();
                    const respContent = chatData.data.content;
                    // 解析【评估】和【下一题】
                    const evalMatch = respContent.match(/【评估】([\s\S]*?)(?=【下一题】|$)/);
                    const nextMatch = respContent.match(/【下一题】([\s\S]*?)$/);
                    let displayText = respContent;
                    nextQuestionText = '';
                    if (nextMatch) {
                        nextQuestionText = nextMatch[1].trim();
                    }
                    addMessage('ai', '🎯 AI 面试官', displayText);
                    // 不自动TTS，显示下一题按钮
                    if (chatData.data.finished) {
                        finished = true;
                        hintText.textContent = '✅ 面试已全部完成！点击按钮重新开始';
                        voiceControls.classList.add('hidden');
                        startBtn.classList.remove('hidden');
                        startBtn.textContent = '🔄 重新面试';
                        startBtn.disabled = false;
                    } else {
                        // 显示"下一题"按钮
                        showNextBtn();
                    }
                } else {
                    hintText.textContent = '❌ 回答处理失败，请重试';
                }
            } catch (e) {
                hintText.textContent = '❌ 网络错误，请重试';
            }

            isProcessing = false;
            micBtn.disabled = false;
        };

        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add('recording');
        hintText.textContent = '🔴 录音中...点击停止结束录音';
        hintText.classList.add('recording');
    } catch (e) {
        hintText.textContent = '❌ 无法访问麦克风，请授权或检查浏览器设置';
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove('recording');
        hintText.classList.remove('recording');
        hintText.textContent = '⏳ 处理中...';
    }
}

// === TTS ===
    // === TTS - 可选回调 ===
    async function playTTS(text, onEnd) {
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
                if (onEnd) audio.onended = onEnd;
                audio.play().catch(function() { if (onEnd) onEnd(); });
            } else {
                if (onEnd) onEnd();
            }
        } catch (e) {
            console.log('TTS play failed:', e);
            if (onEnd) onEnd();
        }
    }

    // === 下一题按钮 ===
    function showNextBtn() {
        // 在底部添加下一题按钮
        const existing = document.getElementById('nextBtn');
        if (existing) existing.remove();
        
        const nextDiv = document.createElement('div');
        nextDiv.id = 'nextBtn';
        nextDiv.className = 'next-btn-wrapper';
        nextDiv.innerHTML = '<button class="next-btn" onclick="onNextQuestion()">📌 下一题</button>';
        document.getElementById('bottomBar').appendChild(nextDiv);
        
        hintText.textContent = '✅ 已回答，点击「下一题」继续';
        micBtn.disabled = true;
    }

    function onNextQuestion() {
        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) nextBtn.remove();
        
        if (finished) {
            hintText.textContent = '🎉 面试已全部完成';
            return;
        }
        
        // TTS播放下一题问题
        if (nextQuestionText) {
            playTTS(nextQuestionText, function() { enableRecording(); });
        } else {
            enableRecording();
        }
    }
    try {
        // 只对AI回复的前500字做语音合成（太长播放体验不好）
        const ttsText = text.length > 500 ? text.substring(0, 500) + '...' : text;
        const resp = await fetch('api/interview/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'message=' + encodeURIComponent(ttsText)
        });
        const data = await resp.json();
        if (data.code === 0 && data.data.audio_url) {
            const audio = new Audio(data.data.audio_url);
            audio.play().catch(() => {});
        }
    } catch (e) {
        // TTS失败不影响主流程
        console.log('TTS play failed:', e);
    }
}

// === UI 辅助函数 ===
function addMessage(role, label, content) {
    // 移除等待动画
    const waiting = document.querySelector('.waiting-anim');
    if (waiting) waiting.remove();

    const div = document.createElement('div');
    div.className = 'msg ' + role;
    div.innerHTML = '<div class="label">' + label + '</div>' + formatContent(content);
    if (role === 'ai') {
        div.innerHTML += '<button class="sound-btn" onclick="playTTS(this.dataset.text)" data-text="' + escapeHtml(content.substring(0, 500)) + '">🔊 听语音</button>';
    }
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
    return div;
}

function updateLastUserMessage(text) {
    const msgs = chatArea.querySelectorAll('.msg.user');
    const last = msgs[msgs.length - 1];
    if (last) {
        last.innerHTML = '<div class="label">👤 你</div>' + formatContent(text);
    }
}

function showWaiting() {
    const w = document.createElement('div');
    w.className = 'waiting-anim';
    w.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    chatArea.appendChild(w);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function formatContent(text) {
    if (!text) return '';
    return escapeHtml(text).replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
</script>
</body>
</html>"""