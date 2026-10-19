# -*- coding: utf-8 -*-
"""生成 docx：需求规格说明书、接口设计、数据库、专家评审、用户手册。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _docxlib import (new_doc, doc_title, doc_subtitle, h1, h2, para, bullet, number_list,
                      table, cover_table, sign_table)

OUT = Path(__file__).parent / "docx"
OUT.mkdir(parents=True, exist_ok=True)


def gen_requirement():
    doc = new_doc()
    doc_title(doc, "需求规格说明书", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent · v1.0")
    h1(doc, "一、引言")
    h2(doc, "1.1 编写目的")
    para(doc, "明确本系统功能/非功能需求，作为设计、开发、测试与验收依据。")
    h2(doc, "1.2 项目背景")
    para(doc, "见任务书与项目提案。核心：自然语言对上传表格进行分析，系统完成理解→计划→执行→图表→结论。")
    h2(doc, "1.3 读者对象")
    para(doc, "开发、测试、干系人、指导教师。")
    h1(doc, "二、用户需求")
    h2(doc, "2.1 用户角色")
    bullet(doc, "业务人员：上传、提问、看结论、导出、追问；")
    bullet(doc, "数据分析师：探索、验证、查看生成代码；")
    bullet(doc, "企业管理员：权限/脱敏、审计。")
    h2(doc, "2.2 用户故事（优先级 P0/P1）")
    table(doc, ["编号", "用户故事", "优先级"],
          [["US-01", "上传表格并用自然语言提问", "P0"],
           ["US-02", "多表上传与自动关联", "P0"],
           ["US-03", "看到问题→代码→结果→图表→结论", "P0"],
           ["US-04", "追问上一轮结果（what-if）", "P0"],
           ["US-05", "一键导出 docx/pdf", "P1"],
           ["US-06", "管理员配置权限与脱敏", "P1"],
           ["US-07", "审计分页查询", "P1"],
           ["US-08", "百万行查询<3s", "P1"]])
    h1(doc, "三、功能需求")
    h2(doc, "FR-1 表格上传")
    para(doc, "支持 .csv/.xlsx/.xls，流式写入，返回 table_id；单文件≤200MB、单表≤100万行。")
    h2(doc, "FR-2 Schema 画像")
    para(doc, "生成列类型、示例值、空值率、基数；多表推断关联键注入 Prompt；画像缓存。")
    h2(doc, "FR-3 分析闭环")
    para(doc, "计划→代码生成→沙箱执行→结果检查→失败反思（≤3轮）→图表与结论。")
    h2(doc, "FR-4 图表与报告")
    para(doc, "自动选图（趋势→折线、占比→饼、对比→柱）；报告导出 docx/pdf 含真实图表，可溯源。")
    h2(doc, "FR-5 追问与假设检验")
    para(doc, "会话上下文；极简追问补全；what-if 基于上轮代码沙箱重跑。")
    h2(doc, "FR-6 多表关联")
    para(doc, "自动发现共同列，merge 为宽表供跨表分析。")
    h2(doc, "FR-7 企业安全")
    para(doc, "敏感列识别脱敏；字段级权限；审计留痕分页查询。")
    h1(doc, "四、非功能需求")
    para(doc, "性能：百万行<3s、一次通过率≥70%（反思后≥90%）；安全：沙箱禁网限资源逃逸拦截100%；"
              "可用性：中文界面结论；可维护：模块化、中文注释、.env 配置；可复现：留痕+报告含代码。")
    h1(doc, "五、约束")
    para(doc, "语言 Python+TypeScript；框架 FastAPI、LangGraph、React、DuckDB、ECharts；模型 DeepSeek+Ollama。")
    h1(doc, "六、验收标准")
    para(doc, "端到端正确率≥85%、一次通过率≥70%（反思后≥90%）、百万行<3s、逃逸拦截100%、报告可溯源。")
    doc.save(str(OUT / "2-1-需求规格说明书.docx"))
    print("生成 2-1-需求规格说明书.docx")


def gen_interfaces():
    doc = new_doc()
    doc_title(doc, "接口设计说明书", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent · REST API")
    h1(doc, "一、接口总览")
    table(doc, ["接口", "方法", "说明"],
          [["/api/tables/upload", "POST", "上传表格,返回table_id"],
           ["/api/tables", "GET", "列出已上传表格"],
           ["/api/tables/{id}/profile", "GET", "返回Schema画像(读缓存)"],
           ["/api/analysis/ask", "POST", "发起自然语言分析"],
           ["/api/analysis/followup", "POST", "追问/假设检验"],
           ["/api/report/{id}/export?fmt=docx|pdf", "GET", "导出报告(含图表)"],
           ["/api/admin/audit?page&size&keyword", "GET", "分页查询审计"],
           ["/api/health", "GET", "健康检查"]])
    h1(doc, "二、通用约定")
    para(doc, "统一 JSON；错误返回 {detail:...}；中文 UTF-8；trace_id 关联审计。")
    h1(doc, "三、各接口详设")
    h2(doc, "3.1 POST /api/tables/upload")
    para(doc, "multipart/form-data，字段 file。返回 table_id/filename/row_count/col_count。")
    h2(doc, "3.2 POST /api/analysis/ask")
    para(doc, "请求 {question, table_ids, session_id}；响应含 plan/code/output/conclusion/charts/report_id/session_id。")
    h2(doc, "3.3 POST /api/analysis/followup")
    para(doc, "请求 {session_id, question}；内部先补全追问再走完整分析，返回与 ask 相同结构。")
    h2(doc, "3.4 GET /api/report/{id}/export")
    para(doc, "查询参数 fmt=docx|pdf；返回文件流，Content-Disposition 用 RFC5987；报告中嵌入真实图表。")
    h2(doc, "3.5 GET /api/admin/audit")
    para(doc, "分页/关键字过滤；返回 {total,page,size,items}。")
    h1(doc, "四、错误码")
    table(doc, ["场景", "HTTP"],
          [["未上传表格", "400"], ["会话不存在", "400"], ["报告不存在", "404"],
           ["不支持格式", "400"], ["未配置Key", "500(明确提示)"]])
    h1(doc, "五、接口数量")
    para(doc, "共约 8 个 REST 接口。")
    doc.save(str(OUT / "2-2-接口设计说明书.docx"))
    print("生成 2-2-接口设计说明书.docx")


def gen_database():
    doc = new_doc()
    doc_title(doc, "数据库说明书", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent · SQLite")
    h1(doc, "一、概述")
    para(doc, "使用 SQLite（data/agent.db）存储：已上传表格元信息（含画像缓存）、审计日志、分析结果。"
              "随应用启动自动建表并做兼容迁移。")
    h1(doc, "二、表结构")
    h2(doc, "（一）tables（已上传表格）")
    table(doc, ["字段", "类型", "说明"], [["table_id","TEXT PK","唯一标识"],["filename","TEXT","文件名"],
          ["stored_path","TEXT","存储路径"],["row_count","INTEGER","行数"],["profile_json","TEXT","画像缓存"],
          ["created_at","TEXT","创建时间"]])
    h2(doc, "（二）audit_log（审计日志）")
    table(doc, ["字段", "类型", "说明"], [["trace_id","TEXT PK","流水号"],["user_name","TEXT","用户"],
          ["action","TEXT","ask/followup/export"],["question","TEXT","问题"],["code","TEXT","代码"],
          ["created_at","TEXT","时间"]])
    h2(doc, "（三）analysis_results（分析结果）")
    table(doc, ["字段", "类型", "说明"], [["report_id","TEXT PK","报告编号"],["session_id","TEXT","会话"],
          ["question","TEXT","问题"],["plan/code","TEXT","计划/代码"],["output","TEXT","结果JSON"],
          ["conclusion","TEXT","结论"],["charts","TEXT","图表JSON"],["created_at","TEXT","时间"]])
    h1(doc, "三、数据访问层")
    para(doc, "db/session.py 统一 get_connection；写操作 commit；提供 get_analysis/list_analysis_by_session/"
              "query_audit/list_tables 等 CRUD。")
    h1(doc, "四、画像缓存与清理")
    para(doc, "上传时画像 json 存 profile_json，分析优先读缓存；.gitignore 忽略 data/*.db，属运行时产物。")
    doc.save(str(OUT / "2-4-数据库说明书.docx"))
    print("生成 2-4-数据库说明书.docx")


def gen_review():
    doc = new_doc()
    doc_title(doc, "专家评审意见及整改结果", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、会议信息")
    para(doc, "时间 2026-__-__；参与：指导教师、全体成员；评审：需求规格、技术方案、接口设计。")
    h1(doc, "二、评审意见与整改结果")
    table(doc,
          ["编号", "意见", "整改", "状态"],
          [["R1", "沙箱安全边界需明确(禁网/资源限额落地)", "独立子进程+白名单+超时强杀", "已整改"],
           ["R2", "极简追问补全需验收标准", "complete_followup 结合上轮代码沙箱重跑", "已整改"],
           ["R3", "报告需嵌真实图表图片", "matplotlib 自绘插入 docx/pdf", "已整改"],
           ["R4", "审计需区分操作类型并分页", "audit_log.action + 分页关键字", "已整改"],
           ["R5", "上传列表刷新丢失/多表批量", "GET /api/tables + input multiple", "已整改"],
           ["R6", "评测集量化正确率", "评测集与指标方案", "已整改"]])
    h1(doc, "三、遗留关注")
    para(doc, "百万行压测、LangGraph 迁移、敏感列脱敏与字段级权限完整落地。")
    doc.save(str(OUT / "2-3-专家评审意见及整改结果.docx"))
    print("生成 2-3-专家评审意见及整改结果.docx")


def gen_manual():
    doc = new_doc()
    doc_title(doc, "用户手册 / 操作手册", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、简介")
    para(doc, "用自然语言对上传的表格做数据分析：上传 Excel/CSV → 提问 → 图表与结论 → 追问/导出。")
    h1(doc, "二、快速开始")
    number_list(doc, ["启动后端与前端（见技术规范）；",
                      "打开 http://localhost:5173；",
                      "上传表格（可多选）；",
                      "输入问题并点『发起分析』；",
                      "查看图表与结论，可追问或导出。"])
    h1(doc, "三、功能使用")
    h2(doc, "3.1 上传表格")
    para(doc, "支持一次选择多个文件；已上传以标签展示可移除；刷新后列表自动恢复。")
    h2(doc, "3.2 自然语言提问")
    para(doc, "示例：“各区域销售额及占比”“华东地区2月的销售额是多少”。")
    h2(doc, "3.3 追问 / 假设检验")
    para(doc, "在追问框输入，如“剔除华东区域会怎样”“一月呢”。")
    h2(doc, "3.4 导出报告")
    para(doc, "点“导出 Word/PDF”下载含问题、结论、数据表、真实图表、代码的报告。")
    h2(doc, "3.5 审计日志")
    para(doc, "点右上角“审计日志”在新窗口分页查看谁/何时/问了什么/跑了什么代码。")
    h2(doc, "3.6 智能体决策过程")
    para(doc, "结果下方点“🔍 智能体决策过程”可查看计划与生成代码。")
    h1(doc, "四、常见问题")
    bullet(doc, "分析较慢？真实大模型需几秒，属正常；")
    bullet(doc, "未出图表？概述型问题（如几行几列）无需图表；")
    bullet(doc, "报告打不开？确认后端已运行。")
    doc.save(str(OUT / "6-用户手册.docx"))
    print("生成 6-用户手册.docx")


gen_requirement()
gen_interfaces()
gen_database()
gen_review()
gen_manual()
