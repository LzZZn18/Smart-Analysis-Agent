"""报告导出接口：把已保存的分析结果导出为 docx 或 pdf。"""
from __future__ import annotations

import json
import urllib.parse
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.db.session import get_analysis, list_analysis_by_session, write_audit
from app.services import reporter

router = APIRouter()

# 支持的中文导出 MIME 类型
_FORMATS = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


def _attachment_header(filename: str) -> str:
    """构造跨 ASCII 安全的 Content-Disposition。

    中文文件名用 RFC 5987 filename* 形式 URL 编码, 避免 latin-1 编码异常。
    """
    ascii_name = filename.encode("ascii", "ignore").decode() or f"report.{'docx' if '.docx' in filename else 'pdf'}"
    quoted = urllib.parse.quote(filename)
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\' \'{quoted}'


@router.get("/report/{report_id}/export")
def export_report(report_id: str, fmt: str = "docx"):
    """把指定 report_id 的分析结果导出为 docx/pdf 文件。

    Args:
        report_id: 分析结果编号（来自 /api/analysis/ask 返回）
        fmt: 导出格式, docx | pdf
    """
    fmt = fmt.lower()
    if fmt not in _FORMATS:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {fmt}（支持 docx/pdf）")

    row = get_analysis(report_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"未找到报告 {report_id}")

    session_id = row.get("session_id")
    if session_id:
        # 取该会话的全部历史（多轮追问的完整对话）, 让报告涵盖此前各轮
        records = list_analysis_by_session(session_id)
    else:
        records = [row]

    # 还原数据库中的 JSON 字段为列表类型（reporter 内部会再解码）
    for rec in records:
        for field in ("plan", "output", "charts"):
            rec[field] = rec.get(field) or ""

    # 生成文件字节
    if fmt == "docx":
        content = reporter.render_docx(records)
        media_type = _FORMATS["docx"]
    else:
        content = reporter.render_pdf(records)
        media_type = _FORMATS["pdf"]

    filename = f"分析报告_{report_id}.{fmt}"

    # 审计留痕：导出报告操作（trace_id 需唯一, 不能复用被导出报告的 report_id）
    write_audit(
        trace_id=uuid.uuid4().hex,  # UNIQUE
        action="export",
        question=f"导出报告 {report_id} ({fmt})",
        code=json.dumps([r.get("question", "") for r in records], ensure_ascii=False),
    )

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": _attachment_header(filename),
        },
    )
