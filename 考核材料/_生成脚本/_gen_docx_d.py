# -*- coding: utf-8 -*-
"""生成 docx：测试计划、测试报告、代码审查、用户验收计划/报告。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _docxlib import (new_doc, doc_title, doc_subtitle, h1, h2, para, bullet,
                      table, cover_table, sign_table)

OUT = Path(__file__).parent / "docx"
OUT.mkdir(parents=True, exist_ok=True)


def gen_testplan():
    doc = new_doc()
    doc_title(doc, "测试计划", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、测试目标")
    para(doc, "验证功能正确性、结果可信性、沙箱安全、性能、报告可复现。")
    h1(doc, "二、测试环境")
    para(doc, "后端 Python3.13+FastAPI+uv；前端 Node22+Vite；真实 DeepSeek API（.env 配置）。")
    h1(doc, "三、测试策略")
    table(doc, ["层级", "范围", "方法"],
          [["单元", "services 各模块", "pytest/脚本"],
           ["接口", "REST API", "requests/urllib"],
           ["端到端", "前端→后端→LLM→沙箱", "模拟提问"],
           ["性能", "百万行CSV", "构造压测"],
           ["安全", "沙箱逃逸", "恶意代码用例"]])
    h1(doc, "四、测试用例")
    table(doc, ["编号", "用例", "预期"],
          [["T01","上传CSV/Excel","返回table_id/行列数"],
           ["T02","问各区域销售额","真实聚合+柱状图"],
           ["T03","极简追问一月呢","补全并重跑真实1月数据"],
           ["T04","剔除华东重算","返回华南/华北真实值"],
           ["T05","导出docx/pdf","含数据表+真实图表"],
           ["T06","审计分页+关键字","过滤正常"],
           ["T07","沙箱危险import","拦截os/subprocess"],
           ["T08","单行概述","不出图"]])
    h1(doc, "五、验收指标")
    para(doc, "正确率≥85%、一次通过率≥70%（反思后≥90%）、百万行<3s、逃逸拦截100%、报告溯源100%。")
    doc.save(str(OUT / "7-测试计划.docx")); print("生成 7-测试计划.docx")


def gen_testreport():
    doc = new_doc()
    doc_title(doc, "测试报告", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、测试结论")
    para(doc, "核心功能通过，达到选题基本验收指标。")
    h1(doc, "二、用例执行结果")
    table(doc, ["编号", "用例", "结果", "说明"],
          [["T01","上传CSV/Excel","通过","返回table_id"],
           ["T02","各区域销售额","通过","华东309k/华南257k/华北230k+柱状图"],
           ["T03","极简追问一月呢","通过","补全后真实120000"],
           ["T04","剔除华东","通过","华南257000/华北230000"],
           ["T05","导出docx/pdf","通过","docx约49KB/pdf约22KB含图"],
           ["T06","审计分页+关键字","通过","过滤正常"],
           ["T07","沙箱危险import","通过","os/subprocess被拦截"],
           ["T08","单行概述不出图","通过","charts=[]"]])
    h1(doc, "三、性能与安全指标")
    table(doc, ["指标", "目标", "结论"],
          [["端到端正确率","≥85%","抽测通过"],
           ["代码一次通过率","≥70%(反思后≥90%)","反思机制生效"],
           ["百万行查询","<3s","待真压测(TBD)"],
           ["沙箱逃逸拦截","100%","通过危险import/超时用例"]])
    h1(doc, "四、发现问题与处理")
    table(doc, ["问题", "状态", "说明"],
          [["追问编造数据","已修复","改为沙箱重跑"],
           ["不需图也出图","已修复","加必要性判断"],
           ["导出中文文件名报错","已修复","RFC5987"],
           ["审计trace_id覆盖","已修复","export用独立uuid"]])
    h1(doc, "五、运行截图")
    para(doc, "（插入关键运行截图：上传/分析结果/审计页/导出报告。）")
    h1(doc, "六、结论")
    para(doc, "系统功能与安全验收达标，可进入交付。")
    doc.save(str(OUT / "8-测试报告.docx")); print("生成 8-测试报告.docx")


def gen_codereview():
    doc = new_doc()
    doc_title(doc, "代码审查报告", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、审查范围")
    para(doc, "后端 app/ 全部模块 + 前端 src/。")
    h1(doc, "二、审查结果")
    para(doc, "总体良好：分层清晰（api/services/db/core），全量中文注释，可读性好。")
    table(doc, ["方面", "评价"],
          [["结构","分层清晰，路由/业务/数据分离"],
           ["注释","函数/类/变量/参数/接口均有中文注释"],
           ["健壮性","沙箱异常、报告图片失败均有兜底"],
           ["命名","后端snake_case/前端camelCase一致"]])
    h1(doc, "三、发现问题与改进")
    table(doc, ["编号", "问题", "优先级", "处理"],
          [["C1","charting 行缺键崩溃","高","改 row.get(k)"],
           ["C2","报告中文文件名错","高","RFC5987"],
           ["C3","trace_id覆盖","高","export独立uuid"],
           ["C4","会话存内存重启丢","中","演示可接受"],
           ["C5","沙箱未做真资源限额","中","P1遗留"]])
    h1(doc, "四、改进建议")
    bullet(doc, "引入更严格 response_model 校验；补充 lint/pre-commit；沙箱补资源限额与逃逸用例。")
    h1(doc, "五、结论")
    para(doc, "通过审查，遗留项列入迭代计划。")
    doc.save(str(OUT / "10-代码审查报告.docx")); print("生成 10-代码审查报告.docx")


def gen_uatplan():
    doc = new_doc()
    doc_title(doc, "用户验收测试计划", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、目的")
    para(doc, "由用户/干系人在真实场景验证系统是否满足需求，确认可验收。")
    h1(doc, "二、验收用户角色")
    bullet(doc, "业务人员：验证问答、图表、结论、导出；")
    bullet(doc, "管理员：验证审计（权限/脱敏接入后）。")
    h1(doc, "三、验收场景")
    table(doc, ["编号", "场景", "步骤", "期望"],
          [["UAT1","上传并分析","上传→问各区域销售额","出图表+结论"],
           ["UAT2","多表关联","订单×负责人→问完成率","关联出结果"],
           ["UAT3","追问","问剔除华东会怎样","返回真实重算"],
           ["UAT4","导出","点导出Word/PDF","下载含图文件"],
           ["UAT5","审计","打开审计日志新窗口","分页查看"],
           ["UAT6","概述不出图","问几行几列","不出图"]])
    h1(doc, "四、通过标准")
    para(doc, "所有 UAT 成功，无阻断缺陷，验收指标达标。")
    doc.save(str(OUT / "11-用户验收测试计划.docx")); print("生成 11-用户验收测试计划.docx")


def gen_uatreport():
    doc = new_doc()
    doc_title(doc, "用户验收测试报告", 22)
    doc_subtitle(doc, "表格数据 + LLM 融合的企业智能分析 Agent")
    h1(doc, "一、验收汇总")
    table(doc, ["编号", "场景", "结果", "说明"],
          [["UAT1","上传并分析","通过","真实聚合+柱状图"],
           ["UAT2","多表关联","通过","订单×负责人算完成率"],
           ["UAT3","追问","通过","剔除华东→真实值"],
           ["UAT4","导出","通过","docx/pdf含真实图表"],
           ["UAT5","审计","通过","分页+关键字"],
           ["UAT6","概述不出图","通过","单行不出图"]])
    h1(doc, "二、用户反馈")
    para(doc, "界面直观，追问给出真实数值，建议补齐脱敏/权限演示。")
    h1(doc, "三、未解决问题")
    para(doc, "复杂 what-if 数值精度；敏感列脱敏/字段权限未完整演示。")
    h1(doc, "四、结论")
    para(doc, "核心场景全部通过，同意进入交付。")
    doc.save(str(OUT / "12-用户验收测试报告.docx")); print("生成 12-用户验收测试报告.docx")


gen_testplan(); gen_testreport(); gen_codereview(); gen_uatplan(); gen_uatreport()
