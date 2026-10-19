# -*- coding: utf-8 -*-
"""按模板格式批量生成考核 .docx 文档。
对齐第21组模板：封面信息 + "一、/（一）/1."编号章节 + Normal 正文 + 表格/签名页。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _docxlib import (new_doc, doc_title, doc_subtitle, h1, h2, para, bullet,
                      number_list, table, cover_table, sign_table)

OUT = Path(__file__).parent / "docx"
OUT.mkdir(parents=True, exist_ok=True)


def _cover(doc, name, group, members, project):
    """生成封面信息块（对齐任务书/提案的封面）。"""
    doc_title(doc, project, 16)
    doc_subtitle(doc, f"组别：{group}　项目：{name}", 12)
    cover_table(doc, [
        ("项目名称", name, "组别", group),
        ("组长", members[0], "成员", "、" .join(members[1:])),
        ("制作日期", "2026-__-__", "版本", "v1.0"),
    ])
    para(doc, "")
    para(doc, "签名：", bold=True)


def gen_taskbook():
    doc = new_doc()
    doc_title(doc, "项目任务书", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent（选题 44）")
    h1(doc, "一、项目基本情况")
    cover_table(doc, [
        ("项目名称", "表格数据+LLM融合的企业智能分析Agent", "组别", "XX"),
        ("制作人", "成员A/成员B/成员C/成员D/成员E/成员F", "审核人", "任课教师"),
        ("项目经理", "成员A", "制作日期", "2026/__/__"),
    ])
    para(doc, "签名：", bold=True)
    h1(doc, "二、项目背景与目标")
    para(doc, "企业数据分析正在被 AI 重塑。本项目构建一个\"表格数据 + LLM 融合\"的企业智能分析 Agent："
              "用户上传本地表格（Excel/CSV，支持多表关联、百万行级），用自然语言提问，Agent 自动完成"
              "表格结构理解 → 分析计划 → 生成并执行代码（沙箱）→ 图表生成 → 结论撰写，支持追问与假设检验、"
              "分析留痕可复现、报告一键导出（docx/pdf），企业版能力含字段级权限与敏感列脱敏。")
    h1(doc, "三、任务内容与阶段划分")
    h2(doc, "第一阶段：表格语义理解与上传（第1周）")
    bullet(doc, "Schema 画像：列类型、示例值、空值率、基数、关联键推断；")
    bullet(doc, "DuckDB 引擎：直读 CSV/Excel，支持百万行级；")
    bullet(doc, "上传接口与自然语言问答闭环。")
    h2(doc, "第二阶段：Agent 闭环与沙箱（第2周）")
    bullet(doc, "分析计划 → 代码生成（DuckDB SQL / pandas）→ 沙箱执行 → 结果检查 → 失败自我修正（最多3轮）；")
    bullet(doc, "代码沙箱安全：独立子进程、禁网络、资源限额、超时强杀；")
    bullet(doc, "多表自动关联。")
    h2(doc, "第三阶段：图表与报告、追问与假设检验（第3周）")
    bullet(doc, "图表自动选型（趋势→折线、占比→饼、对比→柱）并输出 ECharts 配置；")
    bullet(doc, "报告模板化渲染导出 docx/pdf，图表可溯源到生成代码；")
    bullet(doc, "多轮上下文保持与 what-if 假设检验。")
    h2(doc, "第四阶段：企业安全与交付（第4周）")
    bullet(doc, "字段级权限、敏感列自动识别脱敏、全链路审计留痕；")
    bullet(doc, "真实数据集验收、评测集正确率与一次通过率统计；")
    bullet(doc, "完整文档与答辩。")
    h1(doc, "四、项目技术方案")
    para(doc, "Agent 框架 LangGraph（计划-执行-反思）；表格引擎 DuckDB + 表格语义理解；模型 DeepSeek-V4/Qwen3-Max API + Ollama 本地兜底；"
              "可视化 ECharts 自动选型 + 报告模板渲染；安全字段级权限、身份证/手机号正则 + 模型双路脱敏；语言 Python + TypeScript。")
    h1(doc, "五、预期成果")
    bullet(doc, "系统源代码（含中文注释）+ 演示数据集；")
    bullet(doc, "报告导出（docx/pdf）、多表关联、追问/假设检验、审计留痕；")
    bullet(doc, "系统设计报告与评测报告。")
    h1(doc, "六、时间安排")
    para(doc, "第1周：Schema画像 + DuckDB + 单表问答闭环；")
    para(doc, "第2周：Agent 反思循环 + 沙箱 + 多表关联；")
    para(doc, "第3周：图表自动选型 + 报告导出 + 追问与 what-if；")
    para(doc, "第4周：权限脱敏 + 审计 + 真实数据集验收 + 文档答辩。")
    h1(doc, "七、签名页")
    sign_table(doc,
               ["姓名", "岗位", "负责主要开发工作/章节", "签名", "日期", "软件版本号"],
               [["成员A", "架构师/组长", "总体架构/需求规格/项目计划/总结", "成员A", "", "v1.0"],
                ["成员B", "后端工程师", "FastAPI/数据层/接口/审计", "成员B", "", "v1.0"],
                ["成员C", "算法工程师", "Agent/Prompt/LLM/追问补全", "成员C", "", "v1.0"],
                ["成员D", "算法工程师", "沙箱/安全/多表/图表选型", "成员D", "", "v1.0"],
                ["成员E", "数据分析师", "前端/报告/评测集", "成员E", "", "v1.0"],
                ["成员F", "测试/部署工程师", "测试/部署/性能/验收", "成员F", "", "v1.0"]])
    doc.save(str(OUT / "0-任务书.docx"))
    print("生成 0-任务书.docx")


gen_taskbook()
