"""全局配置：集中管理应用常量与可调参数。

配置优先级：环境变量（含 .env 文件）> 类内默认值。
敏感凭证（如 LLM_API_KEY）放 .env 文件, 不写入仓库（.gitignore 已忽略）。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# 项目根目录（TableAgent/）
# config.py 位于 backend/app/core/config.py, parents[3] 即项目根
BASE_DIR = Path(__file__).resolve().parents[3]

# 优先尝试加载 backend/.env（若存在）
_DOTENV = BASE_DIR / "backend" / ".env"
if _DOTENV.exists():
    load_dotenv(_DOTENV)


def _env(key: str, default: str) -> str:
    """读取环境变量, 缺失时返回默认值。"""
    return os.environ.get(key, default)


class Settings:
    """应用配置项。"""

    # 上传表格、缓存画像等数据存放目录
    DATA_DIR: Path = BASE_DIR / "data"

    # 基础信息
    APP_NAME: str = "表格分析Agent"

    # 跨域允许的前端来源
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",   # Vite 开发服务器默认端口
        "http://127.0.0.1:5173",
    ]

    # 表格相关限制
    MAX_UPLOAD_SIZE_MB: int = 200          # 单文件上传上限
    MAX_UPLOAD_ROWS: int = 1_000_000       # 单表最大行数（百万行级）
    ALLOWED_EXTENSIONS: tuple = (".csv", ".xlsx", ".xls")

    # LLM 配置：可通过 .env 覆盖
    #   mock | api | ollama
    LLM_PROVIDER: str = _env("LLM_PROVIDER", "mock")
    LLM_API_BASE: str = _env("LLM_API_BASE", "https://api.deepseek.com/v1")
    LLM_API_KEY: str = _env("LLM_API_KEY", "")
    LLM_MODEL: str = _env("LLM_MODEL", "deepseek-chat")
    OLLAMA_BASE_URL: str = _env("OLLAMA_BASE_URL", "http://localhost:11434")

    # 代码沙箱限制
    SANDBOX_TIMEOUT_SEC: float = 30.0      # 单次执行超时（秒）
    SANDBOX_MEMORY_MB: int = 512           # 内存上限
    SANDBOX_MAX_RETRY: int = 3             # 反思最多重试轮数

    # 分析任务相关
    MAX_ANALYSIS_ROWS: int = 100_000       # 发给 LLM 的结果最大采样行数


settings = Settings()

# 确保数据目录存在
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
