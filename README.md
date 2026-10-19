# 表格数据 + LLM 融合的企业智能分析 Agent（第44选题）

上传本地表格（Excel/CSV，支持多表关联、百万行级），用自然语言提问，Agent 自动完成
**表格结构理解 → 分析计划 → 生成并执行代码（沙箱）→ 图表生成 → 结论撰写**，支持追问、
假设检验、留痕可复现与报告导出。

**当前为项目骨架（v0.1）**：后端接口链路已跑通（上传/画像/分析/审计），前端最小可用；
LLM 用 mock 占位、沙箱为基础版、图表/报告/权限脱敏为后续迭代。

## 目录结构

```
表格分析Agent/
├── backend/                  # Python + FastAPI 后端
│   ├── app/
│   │   ├── main.py           # 应用入口
│   │   ├── core/             # 配置(config) + 数据模型(schemas)
│   │   ├── services/         # 业务：agent / llm / sandbox / schema_profiler
│   │   ├── api/              # 路由：tables / analysis / admin
│   │   └── db/               # SQLite 访问层
│   ├── requirements.txt
│   └── README.md
├── frontend/                 # React + Vite + TypeScript 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/                  # App.tsx（最小界面）
├── data/                     # 上传表格、SQLite 数据库、演示数据
├── .gitignore
└── README.md（本文件）
```

## 快速启动

> 依赖由 **uv** 管理虚拟环境（`.venv` 已创建）。首次使用请先 `uv venv` 创建环境。

### 后端

```bash
cd backend
uv pip install -r requirements.txt   # 安装依赖（已用 uv 创建 .venv）
uv run uvicorn app.main:app --reload --port 8000
# API 文档: http://localhost:8000/docs
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

## 核心 API（已实现）

| 接口 | 方法 | 说明 |
|:---|:---|:---|
| `/api/tables/upload` | POST | 上传表格，返回 table_id |
| `/api/tables/{id}/profile` | GET | 返回 Schema 画像 |
| `/api/analysis/ask` | POST | 自然语言分析（计划→代码→沙箱→图表→结论；支持多表关联） |
| `/api/analysis/followup` | POST | 多轮追问 / what-if 假设检验（基于 session_id） |
| `/api/report/{id}/export?fmt=docx\|pdf` | GET | 报告导出 |
| `/api/admin/audit` | GET | 查询审计日志 |
| `/api/health` | GET | 健康检查 |

## 当前进度（对照实现方案）

已实现：
1. **真实 LLM 接入**：`llm.py` 的 `OpenAICompatibleProvider` 已接通 DeepSeek API（真实中文问答验证通过），`MockProvider` 保底；`config.py` 支持 `.env` 配置
2. **代码沙箱加固**：`sandbox.py` 以独立子进程执行生成代码，`sandbox_worker.py` 白名单 import、裁剪内建、禁 `open`，主服务超时强杀
3. **Agent 反思循环**：`agent.py` 计划→生成代码→沙箱执行→失败反思重试（最多 `SANDBOX_MAX_RETRY` 轮）
4. **图表自动选型**：`charting.py` 按结果特征输出 ECharts option（趋势→折线、占比→饼、对比→柱）
5. **真实数据查询**：沙箱内生成代码用 pandas 读上传表并聚合，结果落入 `result`
6. **报告导出**：`reporter.py` 用 python-docx / reportlab 生成 docx/pdf（含问题、结论、数据表、图表、计划与代码，可复现）
7. **多表关联**：`joiner.py` 自动推断关联键并拼表为宽表，跨表问答验证通过（如"订单×负责人计算完成率"）
8. **多轮追问 / what-if**：`api/analysis.py` 会话上下文；`followup` 基于上轮结果重算，返回 `previous` 上轮结果供前端对比视图

待实现：
- 敏感列脱敏、字段级权限、审计留痕完善
- what-if 数值精确性优化（当前为纯文本推断, 复杂条件可能数值偏差）
- 沙箱内存/禁网络真正限制（当前已超时+白名单）

前端已实现并验证：
- `App.tsx` 支持多表上传、自然语言提问、**ECharts 渲染后端返回的图表**、展示结论与可复现代码
- 通过 Vite proxy 转发 `/api` 到后端，前后端联调（真实 LLM）验证通过

### 真实 LLM 配置（已完成接入）

配置在 `backend/.env`（已复制 `.env.example` 并填入真实 Key, `.env` 已被 .gitignore 忽略不会提交）：

```dotenv
LLM_PROVIDER=api
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-...(你的密钥)
LLM_MODEL=deepseek-chat
# 换本地 ollama: LLM_PROVIDER=ollama, LLM_MODEL=qwen2.5
```

## 开发约定

- 所有代码需写 **中文注释**（函数/类/变量/参数/接口调用等），为考核材料第 18 项重要评分依据
- 后端风格：`ruff` 兼容、`pydantic` 定义模型；前端：React + TS + ECharts
- 部署最终采用 Docker（国内部分 registry 已停运，需注意镜像源配置）
