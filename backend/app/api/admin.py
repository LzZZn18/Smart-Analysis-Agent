"""管理接口：审计日志分页查询（权限/脱敏配置后续补充）。"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.schemas import AuditPage
from app.db.session import query_audit

router = APIRouter()


@router.get("/admin/audit", response_model=AuditPage)
def list_audit(
    page: int = Query(1, ge=1, description="页码, 从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    keyword: str = Query("", description="关键字(匹配用户/操作/问题/代码)"),
):
    """分页查询审计日志。"""
    return query_audit(page=page, size=size, keyword=keyword)


# 权限配置与脱敏策略接口在后续迭代补充
