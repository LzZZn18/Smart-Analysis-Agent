import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";

/** 分析结果的类型定义（与后端 AnalysisResult 对齐） */
interface AnalysisResult {
  question: string;
  plan: string[];
  code: string;
  output: unknown;
  conclusion: string;
  charts: Array<{ chart_type: string; option: Record<string, unknown> }>;
  trace_id: string;
  report_id: string;
  session_id: string;
  previous?: AnalysisResult | null;   // what-if 追问时的上一轮结果
}

/** 已上传的表格 */
interface UploadedTable {
  table_id: string;
  filename: string;
}

/** 用 ECharts 渲染一个 option 的组件 */
function Chart({ option }: { option: Record<string, unknown> }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);             // 按容器初始化 ECharts
    chart.setOption(option);                             // 应用后端生成的 option
    const observer = new ResizeObserver(() => chart.resize()); // 自适应尺寸
    observer.observe(ref.current);
    return () => {
      observer.disconnect();
      chart.dispose();                                   // 卸载时释放资源
    };
  }, [option]);

  return <div ref={ref} style={{ width: "100%", height: 320 }} />;
}

/** 渲染一组图表 */
function ChartList({ charts }: { charts: AnalysisResult["charts"] }) {
  if (!charts || charts.length === 0) {
    return <p style={{ color: "#9aa0b0", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
      （本次为概述型结果，无需图表）
    </p>;
  }
  const typeName: Record<string, string> = {
    bar: "柱状图",
    line: "折线图",
    pie: "饼图",
  };
  return (
    <>
      {charts.map((c, i) => (
        <div key={i} className="chart-wrap">
          <p className="chart-label">
            图表{i + 1} · {typeName[c.chart_type] || c.chart_type}
          </p>
          <Chart option={c.option} />
        </div>
      ))}
    </>
  );
}

/** 主界面组件：上传 → 提问 → 展示结果 → 追问/导出 */
function MainApp() {
  const [tables, setTables] = useState<UploadedTable[]>([]);   // 已上传表格
  const [question, setQuestion] = useState("");                // 主问题
  const [followup, setFollowup] = useState("");                // 追问输入
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);               // 提问请求中
  const [error, setError] = useState("");

  // 启动时拉取已上传的表格, 恢复刷新前上传的列表(表格列表持久化)
  useEffect(() => {
    fetch("/api/tables")
      .then((r) => r.json())
      .then((list) => {
        if (Array.isArray(list) && list.length) {
          setTables(list.map((t) => ({ table_id: t.table_id, filename: t.filename })));
        }
      })
      .catch(() => {/* 后端未就绪时静默忽略 */});
  }, []);

  /** 上传表格文件（支持一次选择多个, 批量逐个上传） */
  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;
    setError("");
    const okList: string[] = [];
    let failed = 0;
    // 逐个上传（后端接口一次只处理一个文件）
    for (const file of files) {
      const form = new FormData();
      form.append("file", file);
      try {
        const resp = await fetch("/api/tables/upload", { method: "POST", body: form });
        const data = await resp.json();
        if (!resp.ok) throw new Error(JSON.stringify(data));
        // 追加到已上传表格列表
        setTables((prev) => [...prev, { table_id: data.table_id, filename: data.filename }]);
        okList.push(`${data.filename}(${data.row_count}行×${data.col_count}列)`);
      } catch (e) {
        failed++;
        setError(`上传失败(${file.name}): ${(e as Error).message}`);
      }
    }
    if (okList.length) {
      alert(`上传成功 ${okList.length} 个：\n` + okList.join("\n") + (failed ? `\n（${failed} 个失败）` : ""));
    }
    // 清空 input 值, 允许重复选择同一文件
    event.target.value = "";
  }

  /** 发起首次/主问题分析 */
  async function handleAsk() {
    if (!question.trim()) { setError("请输入问题"); return; }
    setLoading(true);
    setError("");
    try {
      const resp = await fetch("/api/analysis/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, table_ids: tables.map((t) => t.table_id) }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "分析失败");
      setResult(data);
      setFollowup("");   // 清空上轮追问
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  /** 追问 / what-if 假设检验：带 session_id 调 followup */
  async function handleFollowup() {
    if (!result?.session_id) { setError("请先发起一次分析再追问"); return; }
    if (!followup.trim()) { setError("请输入追问内容"); return; }
    setLoading(true);
    setError("");
    try {
      const resp = await fetch("/api/analysis/followup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: result.session_id, question: followup }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "追问失败");
      setResult(data);        // 显示新一轮(追问后)的分析结果
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  /** 导出当前分析结果为 docx / pdf */
  async function handleExport(fmt: "docx" | "pdf") {
    if (!result?.report_id) { setError("当前没有可导出的分析结果"); return; }
    try {
      // 触发浏览器下载后端生成的文件
      const resp = await fetch(`/api/report/${result.report_id}/export?fmt=${fmt}`);
      if (!resp.ok) { const d = await resp.json().catch(() => ({})); throw new Error(d.detail || "导出失败"); }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `分析报告_${result.report_id}.${fmt}`;
      document.body.appendChild(a);
      a.click();             // 触发下载
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  /** 移除某张已上传表格 */
  function removeTable(tableId: string) {
    setTables((prev) => prev.filter((t) => t.table_id !== tableId));
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">📊 表格分析 Agent</h1>
        <button className="btn btn-ghost" onClick={() => window.open("/?view=audit", "_blank")}>
          📋 审计日志
        </button>
      </div>

      {/* 上传区 */}
      <section className="card">
        <h3 className="step-title">
          <span className="step-badge">1</span> 上传表格（支持多表关联）
        </h3>
        <label className="file-btn">
          📁 选择 Excel / CSV 文件
          <input className="file-input" type="file" multiple accept=".csv,.xlsx,.xls" onChange={handleUpload} />
        </label>
        {tables.length > 0 && (
          <div style={{ marginTop: 12 }}>
            {tables.map((t) => (
              <span key={t.table_id} className="table-chip">
                {t.filename}
                <button className="remove" onClick={() => removeTable(t.table_id)}>✕</button>
              </span>
            ))}
          </div>
        )}
        <p style={{ color: "#9aa0b0", fontSize: 12, margin: "10px 0 0" }}>
          支持上传多个文件，系统会自动识别关联列并拼接分析。
        </p>
      </section>

      {/* 提问区 */}
      <section className="card">
        <h3 className="step-title">
          <span className="step-badge">2</span> 用自然语言提问
        </h3>
        <textarea
          className="input-text"
          value={question}
          onChange={(ev) => setQuestion(ev.target.value)}
          placeholder="例如：各区域销售额及占比"
          rows={2}
        />
        <div style={{ marginTop: 12 }}>
          <button className="btn btn-primary" onClick={handleAsk} disabled={loading}>
            {loading ? "⏳ 分析中…" : "🚀 发起分析"}
          </button>
        </div>
        {error && <div className="error-box">{error}</div>}
      </section>

      {/* 结果展示区 */}
      {result && (
        <section className="card">
          <h3 className="result-title">
            <span className="step-badge">3</span> 分析结果
          </h3>

          <p className="question-line"><b>问题：</b>{result.question}</p>

          {/* 导出按钮 */}
          <div style={{ marginBottom: 12 }}>
            <button className="btn btn-ghost" onClick={() => handleExport("docx")} style={{ marginRight: 8 }}>
              📄 导出 Word
            </button>
            <button className="btn btn-ghost" onClick={() => handleExport("pdf")}>
              📕 导出 PDF
            </button>
          </div>

          {/* 图表 */}
          <ChartList charts={result.charts} />

          {/* 结论 */}
          <div className="conclusion-card">
            <div className="conclusion-label">📌 分析结论</div>
            <p style={{ lineHeight: 1.8, margin: 0 }}>{result.conclusion}</p>
          </div>

          {/* 追问区 */}
          <div className="followup-box">
            <h4 className="step-title" style={{ marginBottom: 4 }}>
              <span className="step-badge">4</span> 继续追问 / 假设检验
            </h4>
            <textarea
              className="input-text"
              value={followup}
              onChange={(ev) => setFollowup(ev.target.value)}
              placeholder="例如：剔除华东区域会怎样？换成环比呢？"
              rows={2}
            />
            <div style={{ marginTop: 12 }}>
              <button className="btn btn-primary" onClick={handleFollowup} disabled={loading}>
                {loading ? "⏳ 计算中…" : "💬 追问 / 假设检验"}
              </button>
            </div>
          </div>

          {/* 智能体决策过程（默认折叠隐藏） */}
          <details className="decision-details">
            <summary className="decision-summary">🔍 智能体决策过程（点开查看）</summary>
            <p style={{ color: "#6b7280", fontSize: 13, margin: "12px 0 4px" }}>
              <b>分析计划：</b>{result.plan.join(" → ")}
            </p>
            <p style={{ color: "#6b7280", fontSize: 13, margin: "8px 0 0" }}><b>生成并执行的代码：</b></p>
            <pre className="decision-code">{result.code}</pre>
          </details>
        </section>
      )}
    </div>
  );
}

/** 单条审计记录类型 */
interface AuditItem {
  trace_id: string;
  user: string;
  action: string;
  question: string;
  code: string;
  created_at: string;
}

/** 审计日志页面：独立窗口展示，支持分页与关键字过滤 */
function AuditPage() {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(20);          // 每页条数
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  /** 拉取某一页的审计数据 */
  async function fetchPage(p: number, kw: string) {
    setLoading(true);
    setError("");
    try {
      const q = new URLSearchParams({ page: String(p), size: String(size) });
      if (kw) q.set("keyword", kw);
      const resp = await fetch(`/api/admin/audit?${q.toString()}`);
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "查询失败");
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  // 首页加载 & 页码变化时刷新
  useEffect(() => {
    fetchPage(page, keyword);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(total / size));
  const actionText: Record<string, string> = {
    ask: "提问",
    followup: "追问",
    export: "导出",
  };
  const actionClass: Record<string, string> = {
    ask: "audit-action-ask",
    followup: "audit-action-followup",
    export: "audit-action-export",
  };

  function goPage(p: number) {
    if (p < 1 || p > totalPages) return;
    setPage(p);
  }

  return (
    <div className="page" style={{ maxWidth: 980 }}>
      <div className="page-header">
        <h1 className="page-title">📋 审计日志</h1>
      </div>

      {/* 搜索栏 */}
      <div className="card" style={{ padding: 16 }}>
        <div className="audit-search">
          <input
            className="input-text"
            value={keyword}
            onChange={(ev) => setKeyword(ev.target.value)}
            placeholder="搜索：用户 / 操作 / 问题 / 代码"
            style={{ maxWidth: 340 }}
          />
          <button className="btn btn-primary" onClick={() => { setPage(1); fetchPage(1, keyword); }}>
            搜索
          </button>
          <button className="btn btn-ghost" onClick={() => { setKeyword(""); setPage(1); fetchPage(1, ""); }}>
            清除
          </button>
        </div>
        {error && <div className="error-box">{error}</div>}
        <p className="audit-stat">共 {total} 条记录</p>

        {/* 表格 */}
        <table className="audit-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>用户</th>
              <th>操作</th>
              <th>问题</th>
              <th>代码（可复现）</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr><td colSpan={5} className="audit-empty">（暂无审计记录）</td></tr>
            )}
            {items.map((it) => (
              <tr key={it.trace_id}>
                <td>{it.created_at}</td>
                <td>{it.user}</td>
                <td>
                  <span className={`audit-action-badge ${actionClass[it.action] || "audit-action-ask"}`}>
                    {actionText[it.action] || it.action}
                  </span>
                </td>
                <td>{it.question}</td>
                <td><pre className="audit-code">{it.code}</pre></td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* 分页 */}
        <div className="audit-pager">
          <button className="btn btn-ghost" onClick={() => goPage(page - 1)} disabled={page <= 1}>← 上一页</button>
          <span>第 {page} / {totalPages} 页</span>
          <button className="btn btn-ghost" onClick={() => goPage(page + 1)} disabled={page >= totalPages}>下一页 →</button>
          {loading && <span style={{ color: "#9aa0b0" }}>加载中…</span>}
        </div>
      </div>
    </div>
  );
}

/** 入口组件：根据 URL 参数决定展示主界面或审计日志页 */
export default function App() {
  const param = new URLSearchParams(window.location.search).get("view");
  if (param === "audit") {
    return <AuditPage />;
  }
  return <MainApp />;
}
