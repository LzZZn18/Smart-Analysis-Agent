"""表格上传与画像接口。"""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.core.config import settings
from app.db.session import get_connection
from app.core.schemas import SchemaProfile, TableInfo
from app.services.schema_profiler import build_profile, read_table

router = APIRouter()


@router.post("/tables/upload", response_model=TableInfo)
def upload_table(file: UploadFile = File(...)):
    """上传一个表格文件，返回表元信息。"""
    # 校验扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}")

    # 生成表标识并保存到 data 目录
    table_id = uuid.uuid4().hex[:12]
    stored_path = settings.DATA_DIR / f"{table_id}{ext}"
    with stored_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)   # 流式写入, 支持大文件

    # 构建画像（骨架：仅确认读取得通）
    df = read_table(stored_path, table_id)
    profile: SchemaProfile = build_profile(df, table_id, file.filename)

    # 记录元数据（含画像缓存）
    conn = get_connection()
    conn.execute(
        "INSERT INTO tables (table_id, filename, stored_path, row_count, profile_json) VALUES (?,?,?,?,?)",
        (table_id, file.filename, str(stored_path), len(df), profile.model_dump_json()),
    )
    conn.commit()
    conn.close()

    return TableInfo(
        table_id=table_id, filename=file.filename,
        row_count=len(df), col_count=len(df.columns),
    )


@router.get("/tables", response_model=list[TableInfo])
def list_tables():
    """列出所有已上传的表格（前端用于刷新后恢复列表）。"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT table_id, filename, row_count FROM tables ORDER BY rowid ASC"
    ).fetchall()
    conn.close()
    return [
        TableInfo(table_id=r["table_id"], filename=r["filename"], row_count=r["row_count"] or 0, col_count=0)
        for r in rows
    ]


@router.get("/tables/{table_id}/profile", response_model=SchemaProfile)
def get_profile(table_id: str):
    """返回某张表的 Schema 画像（优先读缓存, 避免重复计算）。"""
    conn = get_connection()
    row = conn.execute("SELECT filename, stored_path, profile_json FROM tables WHERE table_id=?", (table_id,)).fetchone()
    conn.close()
    if not row:
        raise ValueError(f"表不存在: {table_id}")

    # 命中缓存则直接返回
    if row["profile_json"]:
        return SchemaProfile.model_validate_json(row["profile_json"])

    df = read_table(Path(row["stored_path"]), table_id)
    return build_profile(df, table_id, row["filename"])
