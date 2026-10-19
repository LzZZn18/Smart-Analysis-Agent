# 表格数据+LLM融合的企业智能分析Agent —— 后端服务
"""项目后端入口。

运行方式（项目根目录 backend/ 下）:
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis, admin, report, tables
from app.core.config import settings

# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="上传表格 → 自然语言提问 → 计划/执行/反思 → 图表与结论",
)

# 跨域配置：允许前端(React, 默认5173端口)访问后端
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 允许的前端来源
    allow_credentials=True,
    allow_methods=["*"],                  # 允许全部 HTTP 方法
    allow_headers=["*"],                  # 允许全部请求头
)

# 注册业务路由
app.include_router(tables.router, prefix="/api", tags=["tables"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


@app.get("/", tags=["meta"])
def read_root():
    """健康检查根路径。"""
    return {"app": settings.APP_NAME, "status": "ok", "version": app.version}


@app.get("/api/health", tags=["meta"])
def health_check():
    """供前端/部署探活使用。"""
    return {"status": "alive"}
