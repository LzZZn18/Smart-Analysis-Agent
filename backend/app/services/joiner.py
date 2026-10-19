"""多表关联：在多张上传表之间自动发现关联键并拼接成一张合并表。

原理：
1. 通过 infer_join_keys 找出两两表之间的共同列（关联键）；
2. 用 pandas merge 把多表按共同列横向拼接成“事实宽表”；
3. 合并表落到缓存目录, 供沙箱内 LLM 生成的代码直接查询；
4. 生成一段关联关系说明, 注入 Prompt 让 LLM 理解表如何组合。

局限（骨架版）：按“列名相同”找键，单级 join；复杂业务语义留待后续增强。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.core.config import settings
from app.core.schemas import SchemaProfile
from app.services.schema_profiler import infer_join_keys


def _resolve_join_on(profiles: List[SchemaProfile]) -> str:
    """推断多张表的关联键。返回列名；无法确定则返回空串。"""
    key = infer_join_keys(profiles)
    if not key:
        return ""
    # infer_join_keys 返回形如 "表A.列 = 表B.列" 的表达式, 取公共列名
    first = key[0]
    if "=" in first:
        left = first.split("=")[0].strip()
        return left.split(".")[-1].strip()
    return first


def join_tables(
    frames: Dict[str, pd.DataFrame],
    profiles: List[SchemaProfile],
) -> Tuple[Optional[Path], str]:
    """拼接多表为一张合并表。

    Args:
        frames: {表ID: DataFrame}
        profiles: 对应各表的画像

    Returns:
        (合并表文件路径 或 None, 关联关系说明文本)
    """
    if len(frames) <= 1:
        return None, ""

    ids = list(frames.keys())
    join_on = _resolve_join_on(profiles)
    if not join_on:
        return None, ""

    # 统一所有表存在关联键列，否则跳过
    if any(join_on not in f.columns for f in frames.values()):
        return None, ""

    merged = None
    for tid in ids:
        df = frames[tid]
        if merged is None:
            merged = df.copy()
        else:
            merged = merged.merge(df, on=join_on, how="inner", suffixes=("", f"_{tid[:4]}"))
    if merged is None or merged.empty:
        return None, ""

    # 写合并表到缓存目录
    cache = settings.DATA_DIR / ".cache"
    cache.mkdir(parents=True, exist_ok=True)
    out_path = cache / f"joined_{'_'.join(ids)}.csv"
    merged.to_csv(out_path, index=False)

    explanation = (
        f"已将 {len(ids)} 张表按公共列『{join_on}』关联拼接为一张宽表, 保存于 {out_path.name}。\n"
        f"拼接后列: {list(merged.columns)}; 共 {len(merged)} 行。\n"
        "后续分析请直接读取这张合并表。"
    )
    return out_path, explanation
