# -*- coding: utf-8 -*-
"""生成 docx：部署计划/报告、开发进度、项目总结、维护手册、版权、心得体会、工作列表。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _docxlib import (new_doc, doc_title, doc_subtitle, h1, h2, para, bullet, number_list,
                      table, cover_table, sign_table)

OUT = Path(__file__).parent / "docx"
OUT.mkdir(parents=True, exist_ok=True)


def gen_deployplan():
    doc = new_doc()
    doc_title(doc, "部署计划", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、部署目标")
    para(doc, "在目标服务器稳定运行后端+前端，可被访问。")
    h1(doc, "二、部署架构")
    para(doc, "浏览器 → 反向代理 → 前端静态/Vite；/api → FastAPI 后端(8000) → SQLite 与 DeepSeek API。")
    h1(doc, "三、部署步骤")
    number_list(doc, ["配置 Python3.13 + Node22；",
                      "后端：uv pip install -r requirements.txt，配置 .env 填 Key；",
                      "前端：npm install && npm run build，产物 dist/；",
                      "uvicorn 启动后端；反向代理转发静态与 /api；",
                      "配置 CORS 允许前端来源。"])
    h1(doc, "四、配置项")
    para(doc, ".env：LLM_PROVIDER/API_BASE/API_KEY/MODEL；端口 8000；数据 data/ 需持久化。")
    h1(doc, "五、Docker 与回滚")
    para(doc, "可选 Docker 部署（注意国内镜像源）；备份 data/；保留旧版 dist 便于回滚。")
    doc.save(str(OUT / "13-部署计划.docx")); print("生成 13-部署计划.docx")


def gen_deployreport():
    doc = new_doc()
    doc_title(doc, "部署报告", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、部署环境")
    para(doc, "Windows；Python3.13+uv；Node22；后端 uvicorn:8000；前端 Vite:5173。")
    h1(doc, "二、部署活动")
    table(doc, ["步骤", "操作", "结果"],
          [["1","uv pip install -r requirements.txt","成功"],
           ["2","配置 .env(DeepSeek Key)","成功"],
           ["3","npm install && build","成功"],
           ["4","uvicorn 启动后端","成功"],
           ["5","前端 dev 启动","成功"],
           ["6","/api/health → alive","成功"]])
    h1(doc, "三、验证结果")
    para(doc, "前后端正常，上传→分析→追问→导出→审计全链路可用。")
    h1(doc, "四、问题与解决")
    bullet(doc, "中文路径 CSV 读取 → 回退 pandas；报告中文文件名 → RFC5987。")
    h1(doc, "五、结论")
    para(doc, "系统已成功部署并验证，满足演示要求。")
    doc.save(str(OUT / "14-部署报告.docx")); print("生成 14-部署报告.docx")


def gen_progress():
    doc = new_doc()
    doc_title(doc, "开发进度报告", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、已完成任务")
    table(doc, ["阶段", "任务", "完成", "负责"],
          [["第1周","骨架/Schema画像/DuckDB/上传问答","✅","全员"],
           ["第2周","Agent反思/沙箱/多表/真实LLM","✅","成员C/D"],
           ["第3周","图表/报告/追问/前端ECharts","✅","成员E/C"],
           ["第4周","审计/体验打磨/文档答辩","✅","成员B/E/F"]])
    h1(doc, "二、交付物")
    bullet(doc, "后端：上传/画像/分析/追问/报告/审计/列表接口，沙箱/joiner/charting/reporter/llm；")
    bullet(doc, "前端：上传(多选)、提问、图表、结论、追问、导出、决策过程、审计页；")
    bullet(doc, "报告含真实图表；审计分页；画像缓存。")
    h1(doc, "三、待解决问题")
    bullet(doc, "敏感列脱敏、字段级权限（占位未完整演示）；")
    bullet(doc, "沙箱 CPU/内存/禁网络真限额；")
    bullet(doc, "百万行压测与 50 题评测集统计；")
    bullet(doc, "LangGraph 迁移与 Docker 部署。")
    h1(doc, "四、里程碑达成")
    para(doc, "M1~M4 均已达成。")
    doc.save(str(OUT / "9-开发进度报告.docx")); print("生成 9-开发进度报告.docx")


def gen_summary():
    doc = new_doc()
    doc_title(doc, "项目总结报告", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、项目概述")
    para(doc, "实现上传表格+自然语言问答→自动分析→图表与结论→追问/导出的智能分析 Agent，覆盖选题绝大部分功能。")
    h1(doc, "二、完成情况")
    h2(doc, "2.1 功能")
    bullet(doc, "多文件上传、Schema画像(缓存)、多表关联、Agent闭环(计划-代码-沙箱-反思-图表-结论)；")
    bullet(doc, "真实LLM、追问补全、假设检验重算、图表选型、报告导出(含真实图表/多轮)、审计留痕、前端美化。")
    h2(doc, "2.2 验收指标")
    table(doc, ["指标", "目标", "达成"],
          [["端到端正确率","≥85%","抽测达成"],
           ["一次通过率","≥70%(反思后≥90%)","机制生效"],
           ["百万行查询","<3s","引擎就绪待真压测"],
           ["沙箱逃逸拦截","100%","用例通过"],
           ["报告溯源","100%","报告含代码+真实图表"]])
    h1(doc, "三、学到的经验")
    bullet(doc, "可信性：先计划-执行-反思再展示，避免 LLM 编造；")
    bullet(doc, "极简追问补全结合上轮上下文减少歧义；")
    bullet(doc, "独立子进程+白名单+超时是允许 LLM 写代码的安全底线；")
    bullet(doc, "中文路径与编码需兜底。")
    h1(doc, "四、改进建议")
    bullet(doc, "敏感列脱敏、字段级权限、沙箱真限额、百万行压测、评测集、LangGraph、Docker；")
    bullet(doc, "what-if 复杂场景数值精度。")
    h1(doc, "五、结语")
    para(doc, "项目达成选题核心目标，验证了“LLM+真实执行+留痕”的可信分析模式。")
    doc.save(str(OUT / "15-项目总结报告.docx")); print("生成 15-项目总结报告.docx")


def gen_maintain():
    doc = new_doc()
    doc_title(doc, "维护手册", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、常见问题（FAQ）")
    table(doc, ["问题", "原因", "解决"],
          [["未配置Key",".env缺失/占位","填有效DeepSeek Key"],
           ["前端连不上","后端未启动","启动uvicorn:8000"],
           ["中文路径CSV失败","DuckDB读取","回退pandas"],
           ["报告导出报错","后端500","检查agent.db可写"],
           ["刷新列表丢失","需后端list接口","确认后端运行"]])
    h1(doc, "二、日常维护")
    bullet(doc, "备份 data/；定期清理上传副本与 .cache/；uv pip sync、npm update。")
    h1(doc, "三、配置维护")
    para(doc, ".env：LLM_PROVIDER/API_BASE/API_KEY/MODEL/OLLAMA_BASE_URL/SANDBOX_*，改后重启生效。")
    h1(doc, "四、故障排查")
    number_list(doc, ["看后端进程日志；", "查 data/agent.db；", "用 /api/health 探活；", "按 FAQ 定位。"])
    doc.save(str(OUT / "16-维护手册.docx")); print("生成 16-维护手册.docx")


def gen_copyright():
    doc = new_doc()
    doc_title(doc, "版权和许可文档", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、版权声明")
    para(doc, "本项目源代码版权归第 XX 组所有，用于课程实训。")
    h1(doc, "二、主要开源组件与许可")
    table(doc, ["组件", "用途", "许可证"],
          [["FastAPI/Uvicorn/Starlette","Web框架","MIT"],
           ["Pydantic","数据模型","MIT"],
           ["DuckDB","OLAP引擎","MIT"],
           ["pandas/pyarrow","数据处理","BSD-3/Apache-2.0"],
           ["openpyxl","Excel","MIT"],
           ["python-docx/reportlab/matplotlib","报告","MIT"],
           ["React/Vite/TypeScript","前端","MIT"],
           ["ECharts","图表","Apache-2.0"]])
    h1(doc, "三、合规说明")
    para(doc, "按开源许可证使用并保留声明；DeepSeek API 为商业服务按平台规则付费；不含未授权素材。")
    doc.save(str(OUT / "17-版权和许可文档.docx")); print("生成 17-版权和许可文档.docx")


def gen_experience():
    doc = new_doc()
    doc_title(doc, "小组心得体会", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、整体感受")
    para(doc, "4 周从零搭建了“上传表格→自然语言问答→自动分析→图表与结论→追问/报告→审计”的完整 Agent 产品，"
              "最大收获是理解“让大模型既聪明又可信”的工程方法。")
    h1(doc, "二、技术难点与解决")
    bullet(doc, "真实执行而非脑补：用 LLM 生成代码+沙箱执行，追问改为基于上轮代码重跑；")
    bullet(doc, "极简追问补全：结合上轮上下文把省略句补全，解决歧义；")
    bullet(doc, "沙箱安全：子进程隔离+白名单+超时强杀；")
    bullet(doc, "报告可复现：代码、结果、真实图表一起进 docx/pdf。")
    h1(doc, "三、团队协作")
    para(doc, "6 人按架构/后端/算法/测试分工，职责不重叠，每周评审并整改，达成全部里程碑。")
    h1(doc, "四、经验教训")
    bullet(doc, "尽早接入真实数据与模型，避免假数据掩盖问题；")
    bullet(doc, "Windows 中文路径、编码坑提前规避；文档与代码同步写。")
    h1(doc, "五、展望")
    para(doc, "后续补敏感列脱敏、字段级权限、沙箱真限额、Docker 部署与量化评测，做成可交付的 ChatBI 底座。")
    doc.save(str(OUT / "19-小组心得体会.docx")); print("生成 19-小组心得体会.docx")


def gen_worklist():
    doc = new_doc()
    doc_title(doc, "工作列表", 22)
    doc_subtitle(doc, "第 XX 组 · 表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、工作分工及完成情况")
    table(doc, ["姓名", "岗位", "负责主要开发工作", "完成情况", "工作量"],
          [["成员A","架构师/组长","总体架构/需求规格/项目计划/总结","已完成","约占X%"],
           ["成员B","后端工程师","FastAPI/数据层/接口/审计","已完成","约占X%"],
           ["成员C","算法工程师","Agent/Prompt/LLM/追问补全","已完成","约占X%"],
           ["成员D","算法工程师","沙箱/安全/多表/图表选型","已完成","约占X%"],
           ["成员E","数据分析师","前端/报告/评测集","已完成","约占X%"],
           ["成员F","测试/部署","测试/部署/性能/验收","已完成","约占X%"]])
    h1(doc, "二、说明")
    para(doc, "工作分工实事求是、不重叠；工作量占比可根据实际贡献调整。")
    doc.save(str(OUT / "11-工作列表.docx")); print("生成 11-工作列表.docx")


gen_deployplan(); gen_deployreport(); gen_progress(); gen_summary()
gen_maintain(); gen_copyright(); gen_experience(); gen_worklist()
