"""Pydantic 数据模型：定义接口与内部的类型结构。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------- 表格相关 ----------
class TableInfo(BaseModel):
    """上传成功后的表格元信息。"""
    table_id: str                       # 唯一表标识
    filename: str                       # 原始文件名
    row_count: int                      # 行数
    col_count: int                      # 列数


# ---------- Schema 画像 ----------
class ColumnProfile(BaseModel):
    """单列画像。"""
    name: str                           # 列名
    dtype: str                          # 推断类型：int/float/str/datetime
    sample_values: List[Any] = []       # 示例值（注入 Prompt）
    null_rate: float = 0.0              # 空值率 0~1
    cardinality: int = 0                # 去重基数
    semantics: str = ""                 # 推断业务含义（如 金额/区域）


class SchemaProfile(BaseModel):
    """单张表的完整画像。"""
    table_id: str
    filename: str
    columns: List[ColumnProfile] = []


class AskRequest(BaseModel):
    """发起一次自然语言分析请求。"""
    question: str = Field(..., min_length=1, max_length=2000)  # 用户问题
    table_ids: List[str] = []                                  # 涉及的表
    session_id: str = ""                                       # 会话标识(用于追问/上下文)


class FollowupRequest(BaseModel):
    """多轮追问/假设检验请求。"""
    session_id: str = Field(..., min_length=1)   # 必填：定位历史
    question: str = Field(..., min_length=1, max_length=2000)  # 追问内容


class AnalysisResult(BaseModel):
    """一次分析的结果。"""
    question: str
    plan: List[str] = []             # 分析计划步骤
    code: str = ""                   # 生成并执行的代码
    output: Optional[Any] = None     # 执行结果摘要
    conclusion: str = ""             # 结论
    charts: List[Dict[str, Any]] = []  # ECharts option 列表
    trace_id: str = ""               # 审计关联编号
    report_id: str = ""              # 用于报告导出的编号
    session_id: str = ""             # 会话标识
    previous: Optional["AnalysisResult"] = None  # what-if/追问时的上轮结果
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------- 管理 ----------
class SensitiveConfig(BaseModel):
    """敏感列与脱敏策略配置（占位）。"""
    column: str          # 列名
    strategy: str        # mask/hash/replace
    masked_pattern: str = ""  # 掩码格式


class AuditLog(BaseModel):
    """审计日志条目。"""
    trace_id: str
    user: str = "anonymous"
    action: str = "ask"          # 操作类型: ask/followup/export
    question: str = ""
    code: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditPage(BaseModel):
    """审计日志分页结果。"""
    total: int = 0
    page: int = 1
    size: int = 20
    items: List[AuditLog] = []
