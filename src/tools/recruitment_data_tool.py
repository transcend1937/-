"""
精确招录数据查询工具
数据来源：2025届湖南铁道职业技术学院东校区（原铁科）各铁路局招录数据
"""

import json
from typing import Optional
from langchain.tools import tool

# ============ 原始数据（精确！） ============

RAW_DATA = {
    "广州局": {
        "total": {"male": 385, "female": 73, "total": 458, "male_pct": 84.1, "female_pct": 15.9},
        "majors": {
            "铁道交通运营管理": {"male": 73, "female": 22, "total": 95, "male_pct": 76.8, "female_pct": 23.2},
            "铁道机车运用与维护": {"male": 52, "female": 0, "total": 52, "male_pct": 100.0, "female_pct": 0.0},
            "铁道车辆技术": {"male": 45, "female": 6, "total": 51, "male_pct": 88.2, "female_pct": 11.8},
            "动车组检修技术": {"male": 35, "female": 1, "total": 36, "male_pct": 97.2, "female_pct": 2.8},
            "铁道工程技术": {"male": 36, "female": 0, "total": 36, "male_pct": 100.0, "female_pct": 0.0},
            "城市轨道交通运营管理": {"male": 9, "female": 20, "total": 29, "male_pct": 31.0, "female_pct": 69.0},
            "铁道信号自动控制": {"male": 18, "female": 6, "total": 24, "male_pct": 75.0, "female_pct": 25.0},
            "高速铁路综合维修技术": {"male": 18, "female": 2, "total": 20, "male_pct": 90.0, "female_pct": 10.0},
            "城市轨道交通机电技术": {"male": 18, "female": 0, "total": 18, "male_pct": 100.0, "female_pct": 0.0},
            "城市轨道车辆应用技术": {"male": 13, "female": 3, "total": 16, "male_pct": 81.2, "female_pct": 18.8},
            "城市轨道交通通信信号技术": {"male": 14, "female": 2, "total": 16, "male_pct": 87.5, "female_pct": 12.5},
            "高速铁路施工与维护": {"male": 11, "female": 2, "total": 13, "male_pct": 84.6, "female_pct": 15.4},
            "铁道通信与信息化技术": {"male": 7, "female": 3, "total": 10, "male_pct": 70.0, "female_pct": 30.0},
            "电气自动化技术": {"male": 8, "female": 1, "total": 9, "male_pct": 88.9, "female_pct": 11.1},
            "铁道供电技术": {"male": 8, "female": 1, "total": 9, "male_pct": 88.9, "female_pct": 11.1},
            "城市轨道交通供配电技术": {"male": 4, "female": 3, "total": 7, "male_pct": 57.1, "female_pct": 42.9},
            "机电一体化技术": {"male": 7, "female": 0, "total": 7, "male_pct": 100.0, "female_pct": 0.0},
            "机械设计与制造": {"male": 5, "female": 0, "total": 5, "male_pct": 100.0, "female_pct": 0.0},
            "数控技术": {"male": 2, "female": 1, "total": 3, "male_pct": 66.7, "female_pct": 33.3},
            "现代物流管理": {"male": 2, "female": 0, "total": 2, "male_pct": 100.0, "female_pct": 0.0},
        }
    },
    "南昌局": {
        "total": {"male": 126, "female": 57, "total": 183, "male_pct": 68.9, "female_pct": 31.1},
        "majors": {
            "铁道机车运用与维护": {"male": 27, "female": 5, "total": 32, "male_pct": 84.4, "female_pct": 15.6},
            "铁道交通运营管理": {"male": 17, "female": 13, "total": 30, "male_pct": 56.7, "female_pct": 43.3},
            "动车组检修技术": {"male": 21, "female": 7, "total": 28, "male_pct": 75.0, "female_pct": 25.0},
            "现代物流管理": {"male": 12, "female": 6, "total": 18, "male_pct": 66.7, "female_pct": 33.3},
            "铁道车辆技术": {"male": 5, "female": 7, "total": 12, "male_pct": 41.7, "female_pct": 58.3},
            "城市轨道交通机电技术": {"male": 6, "female": 4, "total": 10, "male_pct": 60.0, "female_pct": 40.0},
            "高速铁路施工与维护": {"male": 6, "female": 2, "total": 8, "male_pct": 75.0, "female_pct": 25.0},
            "城市轨道交通运营管理": {"male": 5, "female": 2, "total": 7, "male_pct": 71.4, "female_pct": 28.6},
            "城市轨道车辆应用技术": {"male": 7, "female": 0, "total": 7, "male_pct": 100.0, "female_pct": 0.0},
            "铁道供电技术": {"male": 3, "female": 3, "total": 6, "male_pct": 50.0, "female_pct": 50.0},
            "铁道信号自动控制": {"male": 2, "female": 3, "total": 5, "male_pct": 40.0, "female_pct": 60.0},
            "铁道工程技术": {"male": 4, "female": 1, "total": 5, "male_pct": 80.0, "female_pct": 20.0},
            "铁道通信与信息化技术": {"male": 3, "female": 0, "total": 3, "male_pct": 100.0, "female_pct": 0.0},
            "机械设计与制造": {"male": 1, "female": 2, "total": 3, "male_pct": 33.3, "female_pct": 66.7},
            "高速铁路综合维修技术": {"male": 2, "female": 1, "total": 3, "male_pct": 66.7, "female_pct": 33.3},
            "智能控制技术": {"male": 2, "female": 0, "total": 2, "male_pct": 100.0, "female_pct": 0.0},
            "城市轨道交通通信信号技术": {"male": 0, "female": 1, "total": 1, "male_pct": 0.0, "female_pct": 100.0},
            "电气自动化技术": {"male": 1, "female": 0, "total": 1, "male_pct": 100.0, "female_pct": 0.0},
            "机电一体化技术": {"male": 1, "female": 0, "total": 1, "male_pct": 100.0, "female_pct": 0.0},
            "机电设备技术": {"male": 1, "female": 0, "total": 1, "male_pct": 100.0, "female_pct": 0.0},
        }
    },
    "上海局": {
        "total": {"male": 84, "female": 3, "total": 87, "male_pct": 96.6, "female_pct": 3.4},
        "majors": {
            "铁道工程技术": {"male": 17, "female": 0, "total": 17, "male_pct": 100.0, "female_pct": 0.0},
            "动车组检修技术": {"male": 16, "female": 0, "total": 16, "male_pct": 100.0, "female_pct": 0.0},
            "铁道机车运用与维护": {"male": 10, "female": 0, "total": 10, "male_pct": 100.0, "female_pct": 0.0},
            "城市轨道车辆应用技术": {"male": 9, "female": 0, "total": 9, "male_pct": 100.0, "female_pct": 0.0},
            "铁道信号自动控制": {"male": 5, "female": 1, "total": 6, "male_pct": 83.3, "female_pct": 16.7},
            "铁道供电技术": {"male": 6, "female": 0, "total": 6, "male_pct": 100.0, "female_pct": 0.0},
            "高速铁路施工与维护": {"male": 5, "female": 0, "total": 5, "male_pct": 100.0, "female_pct": 0.0},
            "城市轨道交通运营管理": {"male": 4, "female": 0, "total": 4, "male_pct": 100.0, "female_pct": 0.0},
            "铁道车辆技术": {"male": 4, "female": 0, "total": 4, "male_pct": 100.0, "female_pct": 0.0},
            "电气自动化技术": {"male": 3, "female": 0, "total": 3, "male_pct": 100.0, "female_pct": 0.0},
            "城市轨道交通供配电技术": {"male": 2, "female": 0, "total": 2, "male_pct": 100.0, "female_pct": 0.0},
            "城市轨道交通通信信号技术": {"male": 0, "female": 2, "total": 2, "male_pct": 0.0, "female_pct": 100.0},
            "机电一体化技术": {"male": 1, "female": 0, "total": 1, "male_pct": 100.0, "female_pct": 0.0},
            "铁道交通运营管理": {"male": 1, "female": 0, "total": 1, "male_pct": 100.0, "female_pct": 0.0},
            "铁道通信与信息化技术": {"male": 1, "female": 0, "total": 1, "male_pct": 100.0, "female_pct": 0.0},
        }
    },
    "武汉局": {
        "total": {"male": 29, "female": 12, "total": 41, "male_pct": 70.7, "female_pct": 29.3},
        "majors": {
            "动车组检修技术": {"male": 9, "female": 1, "total": 10, "male_pct": 90.0, "female_pct": 10.0},
            "铁道供电技术": {"male": 6, "female": 2, "total": 8, "male_pct": 75.0, "female_pct": 25.0},
            "铁道机车运用与维护": {"male": 7, "female": 1, "total": 8, "male_pct": 87.5, "female_pct": 12.5},
            "铁道交通运营管理": {"male": 3, "female": 3, "total": 6, "male_pct": 50.0, "female_pct": 50.0},
            "铁道工程技术": {"male": 2, "female": 2, "total": 4, "male_pct": 50.0, "female_pct": 50.0},
            "铁道信号自动控制": {"male": 0, "female": 2, "total": 2, "male_pct": 0.0, "female_pct": 100.0},
            "铁道车辆技术": {"male": 1, "female": 1, "total": 2, "male_pct": 50.0, "female_pct": 50.0},
            "城市轨道交通机电技术": {"male": 1, "female": 0, "total": 1, "male_pct": 100.0, "female_pct": 0.0},
        }
    }
}

# 所有路局列表
ALL_BUREAUS = list(RAW_DATA.keys())

# 所有专业集合（去重）
ALL_MAJORS = sorted(set(m for b in RAW_DATA.values() for m in b["majors"].keys()))


def format_table(data, title=""):
    """将数据格式化为表格文本"""
    lines = []
    if title:
        lines.append(f"📊 {title}")
        lines.append("")
    
    lines.append("| 路局 | 专业 | 男生 | 女生 | 合计 | 男生占比 | 女生占比 |")
    lines.append("|------|------|-----:|-----:|----:|--------:|--------:|")
    
    for bureau, info in sorted(data.items()):
        for major_name, m_info in sorted(info["majors"].items()):
            lines.append(
                f"| {bureau} | {major_name} | {m_info['male']} | {m_info['female']} | "
                f"{m_info['total']} | {m_info['male_pct']:.1f}% | {m_info['female_pct']:.1f}% |"
            )
        # 路局汇总行
        t = info["total"]
        lines.append(
            f"| **{bureau}** | **合计** | **{t['male']}** | **{t['female']}** | "
            f"**{t['total']}** | **{t['male_pct']:.1f}%** | **{t['female_pct']:.1f}%** |"
        )
        lines.append("|------|------|-----:|-----:|----:|--------:|--------:|")
    
    return "\n".join(lines)


def format_summary(data):
    """汇总格式"""
    lines = ["📊 **各铁路局招录汇总**", ""]
    lines.append("| 路局 | 男生 | 女生 | 总计 | 男女比 |")
    lines.append("|------|-----:|-----:|----:|-------:|")
    grand_m, grand_f, grand_t = 0, 0, 0
    for bureau in ALL_BUREAUS:
        if bureau in data:
            t = data[bureau]["total"]
            lines.append(f"| {bureau} | {t['male']} | {t['female']} | {t['total']} | {t['male_pct']:.1f}% : {t['female_pct']:.1f}% |")
            grand_m += t['male']
            grand_f += t['female']
            grand_t += t['total']
    lines.append(f"| **总计** | **{grand_m}** | **{grand_f}** | **{grand_t}** | **{grand_m/grand_t*100:.1f}% : {grand_f/grand_t*100:.1f}%** |")
    return "\n".join(lines)


@tool
def query_recruitment_data(
    bureau: Optional[str] = None,
    major: Optional[str] = None,
    gender: Optional[str] = None,
    query_type: str = "detail"
) -> str:
    """【优先使用】精确查询2025届湖南铁道职业技术学院东校区（原铁科）各铁路局招录数据。
    
    数据来源：真实招录文件，包含广州局、南昌局、上海局、武汉局4个路局的详细招录数据。
    支持按路局、专业、性别等多维度精确查询，是就业数据查询的首选工具。
    
    Args:
        bureau: 路局名称，可选值：广州局/南昌局/上海局/武汉局，留空查询所有路局
        major: 专业名称，如"铁道机车运用与维护"，留空查询所有专业
        gender: 性别过滤，"male"只看男生，"female"只看女生，留空不过滤
        query_type: 查询类型，"detail"(明细)按专业展示，"summary"(汇总)只显示各局总人数，"compare"(对比)跨局对比
    """
    # 确定要查的路局
    target_bureaus = {}
    if bureau and bureau in RAW_DATA:
        target_bureaus[bureau] = RAW_DATA[bureau]
    elif bureau:
        return f"⚠️ 未找到路局「{bureau}」，当前数据中包含的路局：{'、'.join(ALL_BUREAUS)}"
    else:
        target_bureaus = RAW_DATA  # 查所有
    
    # 如果有专业过滤，只保留匹配的专业
    filtered = {}
    for b_name, b_data in target_bureaus.items():
        majors = b_data["majors"]
        if major:
            # 支持模糊匹配
            matched = {k: v for k, v in majors.items() if major in k}
            if not matched:
                # 尝试全名匹配
                if major in majors:
                    matched[major] = majors[major]
                else:
                    continue
        else:
            matched = dict(majors)
        
        # 性别过滤
        if gender == "male":
            matched = {k: v for k, v in matched.items() if v["male"] > 0}
        elif gender == "female":
            matched = {k: v for k, v in matched.items() if v["female"] > 0}
        
        if matched:
            # 重新计算过滤后的总计
            total_male = sum(m["male"] for m in matched.values())
            total_female = sum(m["female"] for m in matched.values())
            total_all = total_male + total_female
            filtered[b_name] = {
                "total": {
                    "male": total_male,
                    "female": total_female,
                    "total": total_all,
                    "male_pct": round(total_male / total_all * 100, 1) if total_all else 0,
                    "female_pct": round(total_female / total_all * 100, 1) if total_all else 0,
                },
                "majors": matched
            }
    
    if not filtered:
        return f"⚠️ 未找到匹配的数据。当前数据中包含的路局：{'、'.join(ALL_BUREAUS)}"
    
    # 根据query_type返回不同格式
    if query_type == "summary":
        return format_summary(filtered)
    elif query_type == "compare":
        return format_summary(filtered)
    else:
        return format_table(filtered, "2025届湖南铁道职业技术学院东校区铁路局招录数据")