"""数据库访问层（骨架占位）。

规划使用 SQLite 存储：元数据/画像缓存、会话、审计日志、权限配置、
脱敏策略。当前仅提供连接初始化函数, 后续迭代补充建表与 CRUD。
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.core.config import settings

# 数据库文件路径
DB_PATH: Path = settings.DATA_DIR / "agent.db"


def get_connection() -> sqlite3.Connection:
    """获取一个 SQLite 连接（骨架阶段开放, 后续可切换到连接池）。"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据表（含分析结果与审计表）。"""
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tables (
            table_id    TEXT PRIMARY KEY,
            filename    TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            row_count   INTEGER,
            profile_json TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            trace_id  TEXT PRIMARY KEY,
            user_name TEXT,
            question  TEXT,
            code      TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- 分析结果持久化：供报告导出与审计追溯
        CREATE TABLE IF NOT EXISTS analysis_results (
            report_id   TEXT PRIMARY KEY,
            session_id  TEXT,
            question    TEXT,
            plan        TEXT,
            code        TEXT,
            output      TEXT,
            conclusion  TEXT,
            charts      TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        -- 审计日志：谁/何时/问了什么/跑了什么代码/什么操作
        CREATE TABLE IF NOT EXISTS audit_log (
            trace_id   TEXT PRIMARY KEY,
            user_name  TEXT DEFAULT 'anonymous',
            action     TEXT DEFAULT 'ask',
            question   TEXT DEFAULT '',
            code       TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )

    # 兼容性迁移：老版本 audit_log 若缺 action 列则补充
    try:
        conn.execute("ALTER TABLE audit_log ADD COLUMN action TEXT DEFAULT 'ask'")
    except sqlite3.OperationalError:
        pass  # 列已存在

    # 兼容迁移：tables 表补 profile_json 缓存列
    try:
        conn.execute("ALTER TABLE tables ADD COLUMN profile_json TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # 列已存在

    conn.commit()
    conn.close()


def save_analysis(
    report_id: str,
    session_id: str,
    question: str,
    plan: list,
    code: str,
    output: list,
    conclusion: str,
    charts: list,
) -> None:
    """保存一次分析结果到数据库（供报告导出）。"""
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO analysis_results
           (report_id, session_id, question, plan, code, output, conclusion, charts)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            report_id,
            session_id,
            question,
            json.dumps(plan, ensure_ascii=False),
            code,
            json.dumps(output, ensure_ascii=False, default=str),
            conclusion,
            json.dumps(charts, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def get_analysis(report_id: str) -> dict | None:
    """按 report_id 读取一次已保存的分析结果。"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM analysis_results WHERE report_id=?", (report_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def list_analysis_by_session(session_id: str) -> list[dict]:
    """按会话取全部分析记录（按时间正序, 即问答轮次顺序）。

    用于报告导出时还原"多轮追问"的完整对话。
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM analysis_results WHERE session_id=? ORDER BY created_at ASC, rowid ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def write_audit(trace_id: str, action: str, question: str, code: str, user: str = "anonymous") -> None:
    """写入一条审计日志（谁/何时/问了什么/跑了什么代码/什么操作）。"""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO audit_log (trace_id, user_name, action, question, code) VALUES (?,?,?,?,?)",
        (trace_id, user, action, question, code),
    )
    conn.commit()
    conn.close()


def query_audit(page: int = 1, size: int = 20, keyword: str = "") -> dict:
    """分页查询审计日志，支持按关键字过滤（问题/代码/用户/操作类型）。

    Returns:
        {"total": 总数, "items": 当前页记录列表}
    """
    conn = get_connection()
    where = ""
    params: list = []
    if keyword:
        where = ("WHERE user_name LIKE ? OR action LIKE ? OR question LIKE ? OR code LIKE ?")
        like = f"%{keyword}%"
        params = [like] * 4

    total = conn.execute(f"SELECT COUNT(*) FROM audit_log {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM audit_log {where} ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?",
        params + [size, (page - 1) * size],
    ).fetchall()
    conn.close()
    return {"total": total, "page": page, "size": size, "items": [dict(r) for r in rows]}


# 模块导入时自动初始化表结构
init_db()
