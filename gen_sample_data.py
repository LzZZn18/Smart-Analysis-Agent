# -*- coding: utf-8 -*-
"""生成 TableAgent 智能分析 Agent 的示例数据 Excel。
包含两个 sheet，模拟多表关联场景：
  - 销售明细：事实表，逐日销售记录
  - 区域信息：维度表，区域 -> 大区/区域经理
数据埋点：华南区域 2026 Q2 销售额环比大幅下滑（模拟"供应商断货"异常）。
"""
import os
import random
from datetime import date

import pandas as pd

random.seed(42)

# ---------- 维度：区域 ----------
# 区域 -> (大区, 区域经理)
region_meta = {
    "华东": ("东部大区", "陈涛"),
    "华南": ("南部大区", "林晓"),
    "华北": ("北部大区", "王强"),
    "西南": ("西部大区", "赵敏"),
    "华中": ("中部大区", "刘洋"),
    "东北": ("北部大区", "孙丽"),
}

# ---------- 产品 ----------
products = {
    "电子产品": ["智能手机", "笔记本电脑", "平板电脑", "智能手表"],
    "家居用品": ["沙发", "床垫", "灯具", "收纳柜"],
    "服饰": ["T恤", "牛仔裤", "外套", "运动鞋"],
    "食品饮料": ["坚果礼盒", "咖啡豆", "气泡水", "燕麦片"],
}
product_price = {p: random.randint(40, 9000) for items in products.values() for p in items}

cities = {
    "华东": ["上海", "杭州", "南京"],
    "华南": ["广州", "深圳", "厦门"],
    "华北": ["北京", "天津", "青岛"],
    "西南": ["成都", "重庆", "昆明"],
    "华中": ["武汉", "长沙", "郑州"],
    "东北": ["沈阳", "大连", "哈尔滨"],
}

def q(year, quarter):
    """返回某季度起止日期。"""
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    if end_month == 12:
        end = date(year, 12, 31)
    else:
        end = date.fromordinal(date(year, end_month + 1, 1).toordinal() - 1)
    return start, end

rows = []
order_id = 100000

# 生成 2025 Q1 ~ 2026 Q2 共 6 个季度的逐日数据
quarters = [(2026, 1), (2026, 2)]
for year, quarter in quarters:
    start, end = q(year, quarter)
    days = (end - start).days + 1
    # 每天每个区域产生 2~5 笔订单
    for d in range(days):
        day = date.fromordinal(start.toordinal() + d)
        for region, (large, manager) in region_meta.items():
            n_orders = random.randint(1, 2)
            for _ in range(n_orders):
                cat = random.choice(list(products.keys()))
                product = random.choice(products[cat])
                price = product_price[product]
                # 华南区域 2026 Q2 模拟"供应商断货"：销量骤降、单价被抬高
                if region == "华南" and (year, quarter) == (2026, 2):
                    qty = random.randint(1, 3)          # 正常时 5~60
                    unit_price = round(price * random.uniform(1.6, 2.0), 2)
                else:
                    qty = random.randint(5, 60)
                    unit_price = round(price * random.uniform(0.9, 1.1), 2)
                sales = round(qty * unit_price, 2)
                cost = round(sales * random.uniform(0.55, 0.75), 2)
                rows.append({
                    "订单ID": f"SO{order_id}",
                    "订单日期": day.isoformat(),
                    "区域": region,
                    "城市": random.choice(cities[region]),
                    "产品类别": cat,
                    "产品名称": product,
                    "销售数量": qty,
                    "单价": unit_price,
                    "销售额": sales,
                    "成本": cost,
                    "毛利": round(sales - cost, 2),
                })
                order_id += 1

df_detail = pd.DataFrame(rows)

df_region = pd.DataFrame(
    {
        "区域": list(region_meta.keys()),
        "大区": [v[0] for v in region_meta.values()],
        "区域经理": [v[1] for v in region_meta.values()],
    }
)

out_dir = r"C:\Users\Lenovo\Desktop\667\实训3\excel文件"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "销售数据示例.xlsx")
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    df_detail.to_excel(writer, sheet_name="销售明细", index=False)
    df_region.to_excel(writer, sheet_name="区域信息", index=False)

print("生成成功:", out_path)
print("销售明细行数:", len(df_detail))
print("\n各区 2026 Q1 vs Q2 销售额对比（万元）:")
s = df_detail.copy()
s["订单日期"] = pd.to_datetime(s["订单日期"])
s["季度"] = s["订单日期"].dt.to_period("Q")
piv = s.pivot_table(index="区域", columns="季度", values="销售额", aggfunc="sum")
piv = piv[[pd.Period("2026Q1"), pd.Period("2026Q2")]] / 10000
piv["环比"] = (piv[pd.Period("2026Q2")] / piv[pd.Period("2026Q1")] - 1).round(3)
print(piv.round(2))
