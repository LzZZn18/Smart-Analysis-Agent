"""图表自动选型：按结果数据特征选择 ECharts 图表并生成 option JSON。

规则：优先依据结果数据的形状与列的语义推断；
若无法确定, 回退为"表格数据展示"。

输出为符合 ECharts option 结构的 dict, 前端可直接渲染。
"""
from __future__ import annotations

from typing import Any, Dict, List


def _is_numeric(values: List[Any]) -> bool:
    """判断是否为数值列表。"""
    nums = [v for v in values if v is not None and str(v).strip() != ""]
    if not nums:
        return False
    try:
        for v in nums[:10]:
            float(v)
        return True
    except (TypeError, ValueError):
        return False


def auto_choose_chart(output: List[dict]) -> List[Dict[str, Any]]:
    """根据结果数据自动生成一个 ECharts option（骨架版）。

    支持三种最常用形态，后续按实现方案扩展更多类型：
    - 单分类 × 单数值          => 柱状图
    - 时间/趋势 × 数值          => 折线图
    - 分类占比                  => 饼图(局部再演化为占比判断)
    """
    if not output or not isinstance(output[0], dict):
        return []

    keys = list(output[0].keys())
    if len(keys) < 2:
        return []

    # —— 图表必要性判断：不满足则返回 []（不出图）——
    # 1) 只有单行的结果往往是"概述/统计概要", 缺乏多类目对比意义, 不画图
    if len(output) < 2:
        return []

    # 2) 找出可用作横轴的类别列（非数值）。若根本不存在类别列, 无法画分类图
    cat_key = None
    for k in keys:
        vals = [row.get(k) for row in output]   # 容忍某行缺该键
        if not _is_numeric(vals):
            cat_key = k
            break
    if cat_key is None:
        return []                               # 全是数值列, 无类别维度, 不画图

    # 3) 类别基数过小(<=1) 无法形成对比, 不画图
    num_cats = len({_str(row.get(cat_key)) for row in output if row.get(cat_key) is not None})
    if num_cats < 2:
        return []

    # —— 到此才有意义, 选数值列并出图 ——
    # 找到第一个数值列作为纵轴
    val_key = None
    for k in keys:
        vals = [row.get(k) for row in output]   # 容忍某行缺该键
        if _is_numeric(vals) and k != cat_key:
            val_key = k
            break
    if val_key is None:
        return []

    categories = [row.get(cat_key) for row in output]
    values = [row.get(val_key) for row in output]

    # 选型：类别列是否含时间特征（简单按列名启发式）
    lower_cat = str(cat_key).lower()
    is_time = any(t in lower_cat for t in ("date", "time", "month", "year", "日期", "时间", "月", "年"))

    if is_time:
        chart_type = "line"      # 趋势 -> 折线图
    elif len(categories) <= 8:
        # 分类数量少 => 看是否适合饼图（占比语义, 通过列名启发）
        if any(k in lower_cat for k in ("占比", "份额", "share", "ratio", "比例")):
            chart_type = "pie"   # 占比 -> 饼图
        else:
            chart_type = "bar"   # 对比 -> 柱状图
    else:
        chart_type = "bar"       # 分类多也回退柱状图(可滚动)

    # 构造 ECharts option
    if chart_type == "pie":
        data = [{"name": str(c), "value": v} for c, v in zip(categories, values) if v is not None]
        option = {
            "title": {"text": f"{val_key} 占比分布"},
            "tooltip": {"trigger": "item"},
            "series": [{"type": "pie", "data": data}],
        }
    else:
        series_type = "line" if is_time else "bar"
        option = {
            "title": {"text": f"{cat_key} 与 {val_key} 的关系"},
            "tooltip": {},
            "xAxis": {"type": "category", "data": [_str(c) for c in categories]},
            "yAxis": {"type": "value"},
            "series": [{"type": series_type, "data": [v for v in values]}],
        }

    return [{"chart_type": chart_type, "option": option, "xcol": cat_key, "ycol": val_key}]


def _str(v: Any) -> str:
    """安全转为字符串, 处理 None 与特殊类型。"""
    return "" if v is None else str(v)
