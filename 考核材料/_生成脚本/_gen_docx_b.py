# -*- coding: utf-8 -*-
"""生成 docx：项目提案 / 项目计划 / 系统设计 / 技术规范。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _docxlib import (new_doc, doc_title, doc_subtitle, h1, h2, para, bullet,
                      table, cover_table, sign_table)

OUT = Path(__file__).parent / "docx"
OUT.mkdir(parents=True, exist_ok=True)


def gen_proposal():
    doc = new_doc()
    doc_title(doc, "项目提案", 22)
    doc_subtitle(doc, "机器学习 XX 组 · 表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、组成人员")
    para(doc, "组长：成员A")
    para(doc, "组员：成员B、成员C、成员D、成员E、成员F")
    para(doc, "签名：")
    h1(doc, "1. 项目背景")
    para(doc, "企业数据分析正在被 AI 重塑，『会上传 Excel 就能做分析』的 Agent 产品是 2026 年 B 端热门赛道。"
              "传统 BI 学习成本高、交互固定；通用大模型缺少可信与安全的执行结果。本项目建设『表格+LLM』融合的分析 Agent。")
    h1(doc, "2. 项目目标")
    bullet(doc, "上传本地表格（Excel/CSV，多表关联、百万行级）；")
    bullet(doc, "自然语言提问，Agent 完成结构理解→计划→代码执行→图表→结论；")
    bullet(doc, "追问与假设检验、分析留痕可复现、报告一键导出 docx/pdf；")
    bullet(doc, "企业版能力：字段级权限、敏感列脱敏、审计。")
    h1(doc, "3. 技术方案")
    para(doc, "Agent 框架 LangGraph（计划-执行-反思）+ 代码沙箱；表格引擎 DuckDB + 语义理解；"
              "模型 DeepSeek/Qwen API + Ollama 兜底；可视化 ECharts 自动选型；安全字段级权限"
              "+ 身份证/手机号正则与模型双路脱敏；语言 Python + TypeScript。")
    h1(doc, "4. 预期成果与应用")
    bullet(doc, "可运行 Web 系统 v1.0 + 演示数据集 + 完整文档；")
    bullet(doc, "面向数据分析、BI 工程、AI 应用开发岗位；形成可复用的 ChatBI 底座。")
    h1(doc, "5. 时间与风险")
    para(doc, "4 周迭代交付；风险主要为代码生成可靠性与沙箱安全，通过反思循环与多层沙箱控制应对。")
    doc.save(str(OUT / "1-项目提案.docx"))
    print("生成 1-项目提案.docx")


def gen_plan():
    doc = new_doc()
    doc_title(doc, "项目计划 / 项目管理计划", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、项目时间表与阶段划分")
    table(doc,
          ["阶段", "任务", "里程碑/输出", "负责人"],
          [["第1周", "Schema画像+DuckDB+单表问答", "基础问答", "成员B/C"],
           ["第2周", "Agent反思循环+沙箱+多表关联", "可靠分析", "成员C/D"],
           ["第3周", "图表选型+报告导出+追问/what-if", "完整体验", "成员E/C"],
           ["第4周", "权限脱敏+审计+压测+文档答辩", "交付 v1.0", "全员"]])
    h1(doc, "二、甘特图")
    para(doc, "（甘特图：按阶段在时间轴上绘制；见附录 Mermaid Gantt 源码。）")
    para(doc, "```gantt", size=9)
    para(doc, "第1周 基础闭环 | 2026-09-01, 7d", size=9)
    para(doc, "第2周 可靠分析 | 2026-09-08, 7d", size=9)
    para(doc, "第3周 完整体验 | 2026-09-15, 7d", size=9)
    para(doc, "第4周 交付 | 2026-09-22, 7d", size=9)
    para(doc, "```", size=9)
    h1(doc, "三、资源分配")
    bullet(doc, "成员A 架构师/组长：架构、需求规格、进度统筹、总结；")
    bullet(doc, "成员B 后端：FastAPI、数据层、接口、审计；")
    bullet(doc, "成员C 算法：Agent、Prompt、LLM、追问补全；")
    bullet(doc, "成员D 算法：沙箱、安全、多表、图表选型；")
    bullet(doc, "成员E 数据分析：前端、报告、评测集；")
    bullet(doc, "成员F 测试/部署：测试、部署、性能、验收。")
    h1(doc, "四、里程碑")
    bullet(doc, "M1（第1周末）单表问答闭环；M2（第2周末）沙箱+反思+多表；")
    bullet(doc, "M3（第3周末）图表/报告/追问完整演示；M4（第4周末）交付与答辩。")
    h1(doc, "五、风险管理表")
    table(doc,
          ["风险", "影响", "应对"],
          [["LLM 代码错误率高", "高", "Schema注入+反思+降噪"],
           ["API 不稳定", "中", "Ollama 兜底+重试"],
           ["沙箱被绕过", "高", "白名单+禁网+限额+逃逸测试"],
           ["百万行性能", "中", "DuckDB 列式+预聚合"],
           ["工期紧张", "高", "P0→P1 滚动交付+每周评审"]])
    h1(doc, "六、预算")
    para(doc, "大模型 API 按次计费（演示成本低）；开发环境为本机开源工具，预算极低。")
    doc.save(str(OUT / "3-项目计划.docx"))
    print("生成 3-项目计划.docx")


def gen_sysdesign():
    doc = new_doc()
    doc_title(doc, "系统设计文档", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent · 偏技术架构与算法")
    h1(doc, "一、选型综述与对比")
    table(doc,
          ["维度", "选型", "备选", "理由"],
          [["Agent 框架", "LangGraph（规划接入）", "自研循环", "有状态图/反思直观"],
           ["表格引擎", "DuckDB", "pandas+pyarrow", "百万行毫秒级"],
           ["大模型", "DeepSeek API", "Qwen/Ollama", "代码/中文强、便宜"],
           ["沙箱", "独立子进程", "受限 exec", "隔离/超时强杀"],
           ["后端/前端", "FastAPI / React+ECHarts", "Flask/Vue", "异步/生态"],
           ["报告", "python-docx/reportlab/matplotlib", "WeasyPrint", "中文/纯Python"]])
    h1(doc, "二、总体架构")
    para(doc, "交互层（React+ECHarts）→ 编排层（FastAPI：API网关/会话/Agent编排/权限审计）→ "
              "能力层（LLM接入/代码沙箱/图表选型/报告引擎）→ 数据层（DuckDB/pandas、SQLite）。")
    para(doc, "（架构图：交互层→编排层→能力层→数据层的分层结构，见项目 README 的 Mermaid 图。）")
    h1(doc, "三、核心组建设计")
    h2(doc, "（一）Schema 画像（schema_profiler.py）")
    para(doc, "读表（DuckDB 直读 CSV，异常回退 pandas）→ 推断类型/示例值/空值率/基数 → 生成文本画像；"
              "多表关联键按列名相同+值域重叠推断。画像在 SQLite 缓存避免重复计算。")
    h2(doc, "（二）Agent 编排（agent.py）")
    para(doc, "状态 AnalysisState；流程 plan → generate_code → sandbox.execute → 失败 fix_code 反思（≤3轮）"
              "→ auto_choose_chart → write_conclusion；追问基于上轮代码在沙箱内真实重跑。")
    h2(doc, "（三）代码沙箱（sandbox.py / sandbox_worker.py）")
    para(doc, "独立子进程执行；白名单 import、裁剪内建、禁 open、限定 __import__；主服务 timeout 超时强杀；"
              "用户代码与表路径以临时文件传递。")
    h2(doc, "（四）多表关联（joiner.py）")
    para(doc, "自动找共同列 → pandas merge 成宽表 → 关联说明注入 Prompt。")
    h2(doc, "（五）图表选型（charting.py）")
    para(doc, "先必要性判断（≥2行、有类别列、类别基数≥2、有数值列），再按特征选图，输出 ECharts option。")
    h2(doc, "（六）报告引擎（reporter.py）")
    para(doc, "把多轮会话记录渲染为 docx/pdf；每轮含问题、结论、数据表、matplotlib 自绘的真实图表图片、计划与代码。")
    h2(doc, "（七）LLM 接入（llm.py）")
    para(doc, "OpenAICompatibleProvider（DeepSeek/Qwen/Ollama）；complete_followup 做极简追问补全；MockProvider 兜底。")
    h1(doc, "四、数据流")
    para(doc, "上传→画像→多表关联(如有)→计划→代码→沙箱→反思→图表→结论→存 SQLite+审计→返回前端。")
    h1(doc, "五、安全设计")
    para(doc, "沙箱隔离、白名单 import、超时强杀、审计留痕；规划字段级权限与敏感列脱敏。")
    h1(doc, "六、可扩展性")
    para(doc, "LLM/沙箱/报告可替换；存储可迁移 PostgreSQL；支持 Docker 部署。")
    doc.save(str(OUT / "4-系统设计文档.docx"))
    print("生成 4-系统设计文档.docx")


def gen_techspec():
    doc = new_doc()
    doc_title(doc, "技术规范文档", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent · 实现细节")
    h1(doc, "一、技术栈规范")
    table(doc,
          ["层次", "技术", "实测版本", "位置"],
          [["后端", "Python + FastAPI", "3.13 / 0.141", "backend/"],
           ["表格引擎", "DuckDB/pandas/pyarrow", "1.5.5 / 3.0.5 / 25.0.1", "schema_profiler"],
           ["大模型", "DeepSeek API(httpx)", "—", "services/llm.py"],
           ["报告", "python-docx/reportlab/matplotlib", "—", "services/reporter.py"],
           ["前端", "React+Vite+TS+ECharts", "—", "frontend/"],
           ["存储", "SQLite", "内置", "db/session.py"],
           ["依赖管理", "uv", "0.11", "根目录"]])
    h1(doc, "二、后端规范")
    para(doc, "入口 app/main.py；路由 tables/analysis/report/admin；配置集中 core/config.py 支持 .env 覆盖；"
              "数据模型 Pydantic；业务层 services/；数据层 db/session.py 建表+迁移+CRUD+审计分页。")
    para(doc, "代码规范：全量中文注释，函数/类/变量/参数/接口调用均注释，ruff 风格兼容。")
    h1(doc, "三、前端规范")
    para(doc, "React + TypeScript 严格模式；App.tsx 按 ?view=audit 切换主界面/审计页；index.css 统一设计系统；"
              "后端调用经 /api 前缀 + Vite proxy 转发到 8000。")
    h1(doc, "四、环境与启动")
    para(doc, "后端：cd backend && uv pip install -r requirements.txt && uv run uvicorn app.main:app --reload --port 8000；")
    para(doc, "前端：cd frontend && npm install && npm run dev。")
    h1(doc, "五、依赖清单")
    para(doc, "requirements.txt：fastapi、uvicorn、pydantic、httpx、python-docx、reportlab、matplotlib、duckdb、"
              "pandas、pyarrow、openpyxl、python-multipart；package.json：react、echarts、vite、typescript。")
    doc.save(str(OUT / "5-技术规范文档.docx"))
    print("生成 5-技术规范文档.docx")


gen_proposal()
gen_plan()
gen_sysdesign()
gen_techspec()
