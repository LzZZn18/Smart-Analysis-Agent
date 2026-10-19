"""Agent 编排：计划 → 生成代码 → 沙箱执行 → 检查 → 反思 → 图表与结论。

当前实现为命令行式顺序循环（反思最多 settings.SANDBOX_MAX_RETRY 轮）。
规划中可升级为 LangGraph 有状态图，当前 State 结构与划分已预留映射。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.schemas import AnalysisResult, SchemaProfile
from app.services.charting import auto_choose_chart
from app.services.llm import LLMProvider, get_llm
from app.services.sandbox import CodeSandbox
from app.services.schema_profiler import profile_to_prompt


@dataclass
class AnalysisState:
    """一次分析的运行状态（对应 LangGraph 的 State, 便于后续迁移）。"""
    question: str                              # 用户问题
    profiles: List[SchemaProfile] = field(default_factory=list)   # 表画像
    table_paths: Dict[str, str] = field(default_factory=dict)     # 表ID -> 文件路径
    plan: List[str] = field(default_factory=list)                 # 分析计划
    code: str = ""                             # 当前候选代码
    exec_result: Optional[Dict[str, Any]] = None                  # 执行结果
    retry_count: int = 0                       # 反思轮次
    conclusion: str = ""                       # 最终结论
    charts: List[Dict[str, Any]] = field(default_factory=list)    # 图表(ECharts option)


class AnalysisAgent:
    """分析 Agent：串联 LLM、代码沙箱与图表/结论生成。"""

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        sandbox: Optional[CodeSandbox] = None,
    ):
        self.llm = llm or get_llm()
        self.sandbox = sandbox or CodeSandbox()
        self._table_name_hint: str = "[]"   # 每次 ask 前按 table_paths 更新

    def _context(self, profiles: List[SchemaProfile], extra: str = "") -> str:
        """把多表画像（及补充上下文）拼成注入 Prompt 的上下文。"""
        base = "\n\n".join(profile_to_prompt(p) for p in profiles)
        base += f"\n\n【可用的数据源 key（table_paths 的键）】{self._table_name_hint}"
        if extra:
            base += "\n\n【补充上下文】\n" + extra
        return base

    def ask(
        self,
        question: str,
        profiles: List[SchemaProfile],
        table_paths: Optional[Dict[str, str]] = None,
        context_hint: str = "",
        base_code: str = "",
    ) -> AnalysisResult:
        """运行一次完整分析。

        Args:
            question: 用户自然语言问题
            profiles: 各表的 Schema 画像
            table_paths: {表ID: 文件路径}, 供沙箱内生成代码读取真实数据
            context_hint: 额外注入的上下文（如上一轮结论, 用于追问/what-if）
            base_code: 上一轮生成的代码；追问时基于它改条件重跑, 保证数值真实
        """
        state = AnalysisState(
            question=question,
            profiles=profiles,
            table_paths=table_paths or {},
        )
        self._table_name_hint = str(list((table_paths or {}).keys()))
        context = self._context(profiles, context_hint)

        # 1. 生成分析计划
        state.plan = self.llm.plan(question, context)

        # 2. 生成代码并在沙箱执行（失败则反思重试）
        state.code = self.llm.generate_code(question, context, state.plan, base_code=base_code)
        state.exec_result = self.sandbox.execute(state.code, state.table_paths)

        while not state.exec_result["ok"] and state.retry_count < settings.SANDBOX_MAX_RETRY:
            state.retry_count += 1
            error_msg = state.exec_result.get("error") or "未知错误"
            # 携带上一个代码与报错, 让 LLM 反思修正
            state.code = self.llm.fix_code(question, context, state.code, error_msg)
            state.exec_result = self.sandbox.execute(state.code, state.table_paths)

        output: List[dict] = state.exec_result["output"] or []

        # 3. 图表自动选型（按结果数据特征）
        state.charts = auto_choose_chart(output)

        # 4. 生成结论（若拿到图表配置则一并参考）
        if state.exec_result["ok"]:
            if hasattr(self.llm, "write_conclusion_with_chart") and state.charts:
                state.conclusion = self.llm.write_conclusion_with_chart(
                    question, output[: settings.MAX_ANALYSIS_ROWS],
                    str(state.charts[0]),
                )
            else:
                state.conclusion = self.llm.write_conclusion(question, output)
        else:
            state.conclusion = f"分析失败：{state.exec_result.get('error')}（已尝试 {state.retry_count} 次反思）"

        return AnalysisResult(
            question=question,
            plan=state.plan,
            code=state.code,
            output=output,
            conclusion=state.conclusion,
            charts=state.charts,
            trace_id="trace-demo",   # 审计编号后续接入
        )
