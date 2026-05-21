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
    用户说「广铁机考/广铁模拟题/广铁图形推理/广州局机考」等，category='广铁机考模拟题'（不能映射到行测或其他分类）！
    
    Args:
        category: 题目分类。可选值：'行测'、'专业题'、'情景模拟'、'性格测试'、'广铁机考模拟题'(🆕5道图形推理)，或留空进入综合练习
        sub_type: 具体子分类/题型。如专业题下的'铁道机车'、'铁道信号'、'铁道供电'、'铁道工务'、'运输管理'；行测下的'言语理解'、'数量关系'、'判断推理'、'常识判断'
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
        desc = "每天8道精选混合题，保持刷题手感！"
    elif category and sub_type:
        title = f"🔧 **{category}-{sub_type}专项练习** 🚂"
        desc = f"已为你准备好 {category} 分类下的 {sub_type} 专项题目，直击考点！"
    elif category:
        title = f"📊 **{category}分类练习** 🚂"
        desc = f"已为你准备好 {category} 分类的题目，针对性强化训练！"
    else:
        title = "📝 **铁路就业题库刷题平台** 🚂"
        desc = "点击下方链接即可进入刷题："

    return (
        f"{title}\n\n"
        f"{desc}\n\n"
        f"👉 **[开始刷题]({exam_url})**\n\n"
        "### 📋 功能一览\n\n"
        "| 功能 | 说明 |\n"
        "|------|------|\n"
        "| 📋 **分类刷题** | 行测/专业题/情景模拟/性格测试/广铁机考模拟题🆕 |\n"
        "| 🎲 **随机出题** | 综合随机抽题，不限题型 |\n"
        "| 📅 **每日一练** | 每天8道精选题，保持手感 |\n"
        "| 📖 **错题本** | 自动记录错题，随时回顾 |\n"
        "| ⏱ **计时+答题卡** | 全程计时，进度一目了然 |\n\n"
        "### ⌨️ 快捷键\n"
        "- `1-4` 选答案 ｜ `Enter` 提交 ｜ `← →` 切题\n\n"
        "💪 快去刷几道题练练手吧！"
    )