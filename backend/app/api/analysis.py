"""分析接口：自然语言提问 → Agent 分析；多轮追问/假设检验。

会话模型：
- 每次分析产生一个 report_id 并持久化到 SQLite（供报告导出）；
- session_id 用于在多轮对话里保持上下文（追问、what-if）；
- 多表输入时先自动关联拼接为一张宽表，再交给 Agent 分析。
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import APIRouter, HTTPException

from app.core.schemas import AnalysisResult, AskRequest, FollowupRequest, SchemaProfile
from app.db.session import get_connection, save_analysis, write_audit
from app.services.agent import AnalysisAgent
from app.services.joiner import join_tables
from app.services.schema_profiler import build_profile, profile_to_prompt, read_table

router = APIRouter()

# 全局单例 Agent
_agent: AnalysisAgent = AnalysisAgent()

# 会话内存上下文: {session_id: {last_question, last_conclusion, last_output}}
_sessions: Dict[str, dict] = {}


def _make_session_id() -> str:
    """生成一个会话标识。"""
    return uuid.uuid4().hex[:16]


def _load_tables(table_ids: List[str]) -> Tuple[List[SchemaProfile], Dict[str, str], Dict[str, object]]:
    """加载表画像与文件路径。

    返回 (profiles, table_paths, frames), 其中 frames={表ID: DataFrame} 供多表关联。
    """
    profiles: List[SchemaProfile] = []
    table_paths: Dict[str, str] = {}
    frames: Dict[str, object] = {}
    if not table_ids:
        return profiles, table_paths, frames

    conn = get_connection()
    for tid in table_ids:
        row = conn.execute(
            "SELECT filename, stored_path, profile_json FROM tables WHERE table_id=?", (tid,)
        ).fetchone()
        if row:
            df = read_table(Path(row["stored_path"]), tid)
            # 优先用缓存的画像, 避免重复构建
            if row["profile_json"]:
                profiles.append(SchemaProfile.model_validate_json(row["profile_json"]))
            else:
                profiles.append(build_profile(df, tid, row["filename"]))
            table_paths[tid] = row["stored_path"]
            frames[tid] = df
    conn.close()
    return profiles, table_paths, frames


def _require_tables() -> Tuple[List[SchemaProfile], Dict[str, str], Dict[str, object]]:
    """若未指定表, 则把全部已上传表格作为数据源。"""
    conn = get_connection()
    rows = conn.execute("SELECT table_id, filename, stored_path FROM tables").fetchall()
    conn.close()
    profiles: List[SchemaProfile] = []
    table_paths: Dict[str, str] = {}
    frames: Dict[str, object] = {}
    for r in rows:
        df = read_table(Path(r["stored_path"]), r["table_id"])
        profiles.append(build_profile(df, r["table_id"], r["filename"]))
        table_paths[r["table_id"]] = r["stored_path"]
        frames[r["table_id"]] = df
    return profiles, table_paths, frames


def _prepare_data(table_ids: List[str]) -> Tuple[List[SchemaProfile], Dict[str, str], str]:
    """加载并（多表时）拼接数据, 返回 (profiles, table_paths, 额外说明)。

    额外说明：多表关联关系 or 空串。
    """
    profiles, table_paths, frames = _load_tables(table_ids) if table_ids else _require_tables()

    extra = ""
    if len(frames) > 1:
        joined_path, explanation = join_tables(frames, profiles)
        if joined_path is not None:
            # 用合并表替代多张原始表, 作为唯一数据源
            merged_tid = "joined"
            table_paths = {merged_tid: str(joined_path)}
            profiles = [build_profile(read_table(joined_path, merged_tid), merged_tid, joined_path.name)]
            extra = explanation
    return profiles, table_paths, extra


@router.post("/analysis/ask", response_model=AnalysisResult)
def ask_analysis(req: AskRequest):
    """发起一次自然语言分析（或第一轮新对话）。"""
    profiles, table_paths, join_extra = _prepare_data(req.table_ids)
    if not table_paths:
        raise HTTPException(status_code=400, detail="尚未上传任何表格, 请先上传")

    session_id = req.session_id or _make_session_id()

    # 多轮上下文：注入上一轮问题与结论（供追问/what-if 理解）
    hint = ""
    if session_id in _sessions:
        prev = _sessions[session_id]
        hint = (f"上一轮问题：{prev.get('last_question', '')}\n"
                f"上一轮结论：{prev.get('last_conclusion', '')}")
    if join_extra:
        hint = (join_extra + "\n\n" + hint).strip()

    result = _agent.ask(req.question, profiles, table_paths, context_hint=hint)

    # 持久化 & 会话记录
    report_id = uuid.uuid4().hex[:16]
    result.report_id = report_id
    result.session_id = session_id
    save_analysis(
        report_id, session_id, req.question,
        result.plan, result.code, result.output, result.conclusion, result.charts,
    )
    # 审计留痕：谁/何时/问了什么/跑了什么代码
    write_audit(trace_id=report_id, action="ask", question=req.question, code=result.code)
    _sessions[session_id] = {
        "last_question": req.question,
        "last_conclusion": result.conclusion,
        "last_output": result.output,
        "last_code": result.code,
        "last_table_ids": list(req.table_ids),
    }
    return result


@router.post("/analysis/followup", response_model=AnalysisResult)
def followup_analysis(req: FollowupRequest):
    """多轮追问 / 假设检验（与首次提问完全相同的真实流程）。

    会沿用上一轮用到的同一批表、并以上一轮生成的代码为基础，
    让 LLM 在其上修改条件后在沙箱内真实重跑，拿到真实数值；
    同时把上轮问题/结论作为记忆注入 Prompt 作为上下文引导。
    """
    if req.session_id not in _sessions:
        raise HTTPException(status_code=400, detail="会话不存在或已过期, 请重新发起分析")

    prev = _sessions[req.session_id]

    # 沿用上一轮用到的表（与首次 ask 相同的加载与（多表）关联流程）
    profiles, table_paths, join_extra = _prepare_data(prev.get("last_table_ids", []) or [])
    if not table_paths:
        raise HTTPException(status_code=400, detail="找不到上一轮的数据表, 请重新上传并分析")

    # 多轮记忆 + 上一轮代码（供 LLM 基于它改条件真实重跑）
    hint = (f"上一轮问题：{prev.get('last_question', '')}\n"
            f"上一轮结论：{prev.get('last_conclusion', '')}")
    if join_extra:
        hint = (join_extra + "\n\n" + hint).strip()
    base_code = prev.get("last_code", "")

    # —— 追问补全：把"一月呢"这类极简追问还原为完整自包含问题 ——
    # 先基于数据画像构造上下文, 结合上一轮问题/结论, 让 LLM 补齐省略信息
    schema_ctx = "\n\n".join(profile_to_prompt(p) for p in profiles)
    resolved_question = _agent.llm.complete_followup(
        req.question,
        prev.get("last_question", ""),
        prev.get("last_conclusion", ""),
        schema_ctx,
    )

    result = _agent.ask(resolved_question, profiles, table_paths, context_hint=hint, base_code=base_code)

    # 持久化 & 更新会话（含新的代码与表）
    report_id = uuid.uuid4().hex[:16]
    result.report_id = report_id
    result.session_id = req.session_id
    save_analysis(
        report_id, req.session_id, resolved_question,
        result.plan, result.code, result.output, result.conclusion, result.charts,
    )
    # 审计留痕：追问也算一次分析操作
    write_audit(trace_id=report_id, action="followup", question=req.question, code=result.code)
    _sessions[req.session_id] = {
        "last_question": resolved_question,
        "last_conclusion": result.conclusion,
        "last_output": result.output,
        "last_code": result.code,
        "last_table_ids": prev.get("last_table_ids", []),
    }
    return result
