"""铁路院校模拟面试 - AI 面试官 Agent"""

import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.log.write_log import request_context
from storage.memory.memory_saver import get_memory_saver
from interview.questions import INTERVIEW_QUESTIONS

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话（40 条消息）
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口：只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


# ============== 工具定义 ==============

@tool
def get_interview_questions() -> str:
    """获取所有面试题目及参考答案，返回JSON格式的题目列表"""
    return json.dumps(INTERVIEW_QUESTIONS, ensure_ascii=False, indent=2)


# 用于存储更优秀回答的缓存
_better_answers: list[dict] = []

@tool
def record_better_answer(question_id: int, user_answer: str, reason: str) -> str:
    """当面试者的回答明显优于参考答案时，记录优秀回答。
    
    Args:
        question_id: 题目ID
        user_answer: 面试者的优秀回答原文
        reason: 为什么这个回答更优秀
    """
    global _better_answers
    _better_answers.append({
        "question_id": question_id,
        "question": next((q["question"] for q in INTERVIEW_QUESTIONS if q["id"] == question_id), ""),
        "user_answer": user_answer,
        "reason": reason
    })
    return f"✅ 已收录第 {question_id} 题的优秀回答！"


def get_better_answers() -> list[dict]:
    """获取所有收录的优秀回答（供外部使用）"""
    return _better_answers.copy()


def build_agent(ctx=None):
    """构建 AI 面试官 Agent"""
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=[get_interview_questions, record_better_answer],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )