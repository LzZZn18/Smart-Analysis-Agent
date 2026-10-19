# -*- coding: utf-8 -*-
"""生成 6 名成员的个人工作列表 docx（分工不重叠，实事求是）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _docxlib import new_doc, doc_title, doc_subtitle, para, h1, table

OUT = Path(__file__).resolve().parent.parent / "个人材料"
OUT.mkdir(parents=True, exist_ok=True)

# (成员, 学号占位, 岗位, [具体工作])
WORK = {
    "成员A": ("202241XXXXXX1", "架构师 / 组长",
      ["系统总体架构设计与技术选型（LangGraph/DuckDB/React 等选型对比）",
       "需求规格说明书、项目计划与甘特图、风险管理表编写",
       "模块划分、接口契约定义、进度与会议统筹、答辩材料组织",
       "项目总结报告与考核材料整理"]),
    "成员B": ("202241XXXXXX2", "后端工程师",
      ["FastAPI 应用搭建与路由注册（tables/analysis/report/admin）",
       "SQLite 数据层设计：建表、迁移、画像缓存、CRUD 与分页",
       "上传/画像/表格列表/审计等接口实现",
       "接口设计说明书、数据库说明书撰写"]),
    "成员C": ("202241XXXXXX3", "算法工程师",
      ["Agent 编排（计划—执行—反思循环）实现",
       "LLM 接入（OpenAI 兼容 Provider）与 Prompt 工程",
       "极简追问补全（complete_followup）与基于上轮代码重跑",
       "需求规格说明书功能需求部分、系统设计文档算法部分"]),
    "成员D": ("202241XXXXXX4", "算法工程师",
      ["代码沙箱加固（独立子进程、白名单 import、超时强杀）",
       "沙箱逃逸用例与安全测试",
       "多表关联（joiner）与图表自动选型（charting）",
       "系统设计文档安全部分、代码审查报告"]),
    "成员E": ("202241XXXXXX5", "数据分析师",
      ["React + TypeScript + ECharts 前端开发与界面设计",
       "图表渲染、审计日志页、上传/追问交互",
       "报告导出（matplotlib 真实图表嵌入 docx/pdf）",
       "用户手册、评测集与正确率统计方案"]),
    "成员F": ("202241XXXXXX6", "测试 / 部署工程师",
      ["测试计划与测试报告编写、测试用例设计与执行",
       "接口/端到端/安全/性能测试与问题定位",
       "部署计划与部署报告、环境搭建与 health 探活",
       "用户验收测试计划/报告、维护手册"]),
}

def gen():
    for i, (name, (sid, role, items)) in enumerate(WORK.items(), 1):
        doc = new_doc()
        doc_title(doc, "工作列表", 22)
        doc_subtitle(doc, f"第 XX 组 · {sid} · {name} · {role}")
        para(doc, "项目：表格数据 + LLM 融合的企业智能分析 Agent")
        para(doc, "")
        h1(doc, "一、工作分工及完成情况")
        # 构造表格: 序号 / 负责工作 / 完成情况 / 工作量占比
        rows = [[str(j), it, "已完成", "约 __%"] for j, it in enumerate(items, 1)]
        table(doc, ["序号", "负责的主要开发工作 / 内容", "完成情况", "工作量占比"], rows)
        para(doc, "")
        para(doc, "（工作量与完成情况如实填写，分工与其他成员不重叠。）", size=10)
        para(doc, "")
        para(doc, "签　名：____________")
        para(doc, "日　期：2026 年 __ 月 __ 日")
        doc.save(str(OUT / f"{sid}-{name}-工作列表.docx"))
        print(f"生成 {sid}-{name}-工作列表.docx")

gen()
print("=== 6 份个人工作列表生成完毕 ===")
