"""代码沙箱：在受限子进程中执行 LLM 生成的代码。

安全策略：
- 以独立 Python 子进程运行 worker(sandbox_worker.py)，失败/超时不影响主服务；
- 子进程内裁剪内建并禁用危险模块，白名单 import；
- 主服务通过 subprocess 的 timeout 实现超时强杀；
- 用户代码与表路径映射以临时文件传递，避免命令行注入。

数据约定（传递给生成代码的变量）：
    table_paths : dict[表ID, 文件路径]
    table_names : list[表ID]
生成代码最终把结果放入变量 result（值为 list[dict]）。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings

# worker 脚本的绝对路径（与本文件同目录）
WORKER_PATH = Path(__file__).resolve().parent / "sandbox_worker.py"


class CodeSandbox:
    """受限 Python 子进程执行环境。"""

    def execute(self, code: str, table_paths: Dict[str, str]) -> Dict[str, Any]:
        """在受限子进程中执行生成代码。

        Args:
            code: LLM 生成的 Python 代码
            table_paths: {表ID: 文件路径}，供生成代码读取表格
        """
        # 用临时目录隔离工作文件, 避免污染 data 目录
        with tempfile.TemporaryDirectory(prefix="sandbox_") as tmpdir:
            user_code_file = Path(tmpdir) / "user_code.py"
            paths_file = Path(tmpdir) / "table_paths.json"
            user_code_file.write_text(code, encoding="utf-8")
            paths_file.write_text(json.dumps(table_paths, ensure_ascii=False), encoding="utf-8")

            cmd = [
                sys.executable,
                str(WORKER_PATH),
                str(user_code_file),
                str(paths_file),
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",      # 非 UTF-8 字节以替换符处理, 避免解码中断
                    timeout=settings.SANDBOX_TIMEOUT_SEC,
                )
            except subprocess.TimeoutExpired:
                return {
                    "ok": False,
                    "output": None,
                    "error": f"执行超时（>{settings.SANDBOX_TIMEOUT_SEC}s）",
                }
            except Exception as exc:  # 子进程启动失败
                return {"ok": False, "output": None, "error": f"沙箱启动失败: {exc}"}

            # 解析 worker 打印的结果：标记行 __RESULT__ 之后是 JSON
            stdout = proc.stdout or ""
            marker = "__RESULT__"
            if marker in stdout:
                try:
                    payload = json.loads(stdout.split(marker, 1)[1])
                    result = payload.get("result")
                    return {"ok": True, "output": result if isinstance(result, list) else [], "error": None}
                except json.JSONDecodeError:
                    return {"ok": False, "output": None, "error": f"结果解析失败:\n{stdout[-500:]}"}

            # 没有标记 => worker 报错（受限内建/语法错误等）
            err_text = (proc.stderr or stdout or "").strip()
            return {"ok": False, "output": None, "error": err_text[-1000:] or "未知执行错误"}
