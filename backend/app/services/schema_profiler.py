"""Schema 画像：解析上传表格，生成供 LLM 理解的列级画像。

骨架阶段提供：
- CSV/Excel 的读取与基础类型推断
- 示例值、空值率、基数等画像字段
- 关联键推断（多表时按列名 + 值域重叠度简单聚合）

依赖 pyarrow（DuckDB 底层）处理大文件。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import duckdb
import pandas as pd

from app.core.config import settings
from app.core.schemas import ColumnProfile, SchemaProfile


def read_table(filepath: Path, table_id: str) -> pd.DataFrame:
    """读取 CSV/Excel 表格到 DataFrame（使用 DuckDB 保证百万行级性能）。"""
    ext = filepath.suffix.lower()

    if ext == ".csv":
        try:
            # DuckDB 直读 CSV，支持大文件（对中文路径可能报 IO Error, 见下回退）
            con = duckdb.connect()
            df = con.execute(f"SELECT * FROM read_csv_auto('{filepath.as_posix()}')").df()
            con.close()
        except duckdb.Error:
            # 兜底：中文路径等导致 DuckDB 读取失败时改用 pandas 读取
            df = pd.read_csv(filepath)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(filepath)           # 读取 Excel
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    # 裁剪到允许的最大行数，避免资源被耗尽
    return df.head(settings.MAX_UPLOAD_ROWS)


def _infer_dtype(series: pd.Series) -> str:
    """根据 pandas dtype 推断简化类型标签。"""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "int" if pd.api.types.is_integer_dtype(series) else "float"
    return "str"


def build_profile(df: pd.DataFrame, table_id: str, filename: str) -> SchemaProfile:
    """为单张表构建 Schema 画像。"""
    columns: List[ColumnProfile] = []
    n = len(df) if len(df) > 0 else 1

    for col in df.columns:
        series = df[col]
        non_null = series.dropna()

        col_profile = ColumnProfile(
            name=str(col),
            dtype=_infer_dtype(series),
            sample_values=non_null.head(5).tolist(),       # 取前 5 个示例值
            null_rate=round(1 - len(non_null) / n, 4),     # 空值率
            cardinality=int(non_null.nunique()) if len(non_null) else 0,  # 基数
        )
        columns.append(col_profile)

    return SchemaProfile(table_id=table_id, filename=filename, columns=columns)


def infer_join_keys(profiles: List[SchemaProfile]) -> List[str]:
    """多表关联键推断（骨架版：按列名相同 + 非空值域重叠度聚合）。

    完整版应由 LLM 结合业务含义二次确认。
    """
    joins: List[str] = []
    for i in range(len(profiles)):
        for j in range(i + 1, len(profiles)):
            for c1 in profiles[i].columns:
                for c2 in profiles[j].columns:
                    # 列名相同且非数值列（ID/类别列才有关联意义）
                    if c1.name == c2.name and c1.dtype in ("str", "int", "datetime"):
                        joins.append(f"{profiles[i].table_id}.{c1.name} = {profiles[j].table_id}.{c2.name}")
    return joins


def profile_to_prompt(profile: SchemaProfile) -> str:
    """把 Schema 画像转成可直接注入 Prompt 的文本。"""
    lines = [f"表 {profile.table_id} ({profile.filename}):"]
    for c in profile.columns:
        samples = ", ".join(repr(s) for s in c.sample_values[:3])
        lines.append(
            f"  - {c.name} [{c.dtype}] 空值率{c.null_rate} 基数{c.cardinality} "
            f"示例[{samples}] 含义={c.semantics or '未知'}"
        )
    return "\n".join(lines)
