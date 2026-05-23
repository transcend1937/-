"""题库入口工具 - 提供刷题平台的访问入口，支持深链接跳转"""

import os
from langchain.tools import tool


@tool
def open_exam_platform(
    category: str = "",
    sub_type: str = "",
    mode: str = "",
    count: int = 0,
) -> str:
    """打开铁路就业题库刷题平台，支持深链接一键直达指定刷题模式。当用户想要刷题、练习、做题目、准备笔试或考试时，使用此工具。

    【重要分类映射规则 - 必须遵守】
    用户说「模考/模拟考试/限时模考」→ category='广铁机考限时模拟'；用户说「练图形推理/数字推理/言语理解/文学常识」→ category='分层训练', sub_type='题型名'
    
    Args:
        category: 题目分类。可选值：'广铁机考限时模拟'（全真模拟45分钟100分）、'分层训练'（按题型刷题），或留空进入题库首页
        sub_type: 分层训练的子题型。可选值：'图形推理'、'数字推理'、'言语理解'、'高中数学'、'高中物理'、'文学常识'、'地理常识'、'数学物理'、'综合'
        mode: 刷题模式。'daily'表示每日一练，留空表示普通练习
        count: 题目数量，0表示使用默认值(15)
    """
    domain = os.getenv("COZE_PROJECT_DOMAIN_DEFAULT", "http://localhost:5000")
    base_url = f"{domain}/exam/"

    # 构建带参数的URL
    params = []
    if category:
        params.append(f"category={category}")
    if sub_type:
        params.append(f"type={sub_type}")
    if mode:
        params.append(f"mode={mode}")
    if count > 0:
        params.append(f"count={count}")

    if params:
        exam_url = base_url + "?" + "&".join(params)
    else:
        exam_url = base_url

    # 根据参数生成个性化推荐文案
    if mode == "daily":
        title = "📅 **每日一练** 🚂"
        desc = "每天随机抽题，保持刷题手感！"
    elif category == "广铁机考限时模拟":
        title = "🎯 **广铁机考全真模拟** 🚂"
        desc = "已为你准备全真模拟考试！45分钟限时，45道题满分100分，交卷立即出分！"
    elif category and sub_type:
        title = f"📚 **{sub_type}专项训练** 🚂"
        desc = f"已为你准备好 {sub_type} 分类的题目，逐题攻破！"
    elif category:
        title = f"📚 **{category}** 🚂"
        desc = f"已为你准备好 {category} 分类的内容，针对性强化训练！"
    else:
        title = "🚂 **铁路就业智能题库** 🚂"
        desc = "点击下方链接进入题库，选择模拟考试或分层训练："

    return (
        f"{title}\n\n"
        f"{desc}\n\n"
        f"👉 **[开始刷题]({exam_url})**\n\n"
        "### 📋 功能一览\n\n"
        "| 功能 | 说明 |\n"
        "|------|------|\n"
        "| 🎯 **广铁机考限时模拟** | 45分钟全真模考，45题满分100分 |\n"
        "| 📚 **分层训练** | 按题型专项训练，逐题攻破 |\n"
        "| 📖 **错题集** | 自动记录错题，随时回顾强化 |\n"
        "| ⏱ **模拟计时** | 45分钟倒计时，还原真实考场 |\n"
        "| 🎯 **智能出分** | 交卷立刻出分，每题附解析 |\n\n"
        "### ⌨️ 快捷键\n"
        "- `1-4` 选答案 ｜ `Enter` 提交 ｜ `← →` 切题\n\n"
        "💪 快去刷几道题练练手吧！"
    )