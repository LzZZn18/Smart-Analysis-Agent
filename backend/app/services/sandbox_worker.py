"""沙箱 worker：在受限命名空间中执行用户生成的代码。

由 CodeSandbox 以子进程方式调用：
    python sandbox_worker.py <user_code.py> <table_paths.json>

安全措施：
- 提供受限的 __import__（仅白名单模块）；
- 裁剪内置函数（禁 open 等危险入口）；
- 用户代码读取 table_paths / table_names 两个变量；
- 执行后把变量 result 打印为 `__RESULT__{json}` 供主进程回收。
"""
from __future__ import annotations

import json
import sys

# 允许用户代码 import 的模块白名单
_ALLOWED_MODULES = {
    "pandas", "duckdb", "numpy", "json", "datetime",
    "re", "math", "statistics", "collections", "decimal", "functools", "itertools",
}


class SafeImporter:
    """受限 __import__：只放行白名单模块。"""

    @staticmethod
    def __import__(name, globals=None, locals=None, fromlist=(), level=0):
        # 取顶层模块名判断是否在白名单
        top = name.split(".")[0]
        if top not in _ALLOWED_MODULES:
            raise ImportError(f"模块 '{name}' 不在沙箱白名单中，已禁止导入")
        return __import__(name, globals, locals, fromlist, level)


# 构建受限内建：保留安全内建, 用受限 __import__ 替换, 并禁用 open
_BUILTINS = {}
for _k in (
    "len", "str", "int", "float", "list", "dict", "tuple", "set", "bool",
    "range", "sum", "min", "max", "abs", "round", "enumerate", "zip", "map",
    "filter", "sorted", "reversed", "type", "isinstance", "issubclass", "repr",
    "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
    "hasattr", "getattr", "setattr", "callable", "len",
):
    if hasattr(__builtins__, _k) or _k in __builtins__:
        _BUILTINS[_k] = (getattr(__builtins__, _k)
                         if hasattr(__builtins__, _k) else __builtins__[_k])
_BUILTINS["__import__"] = SafeImporter.__import__


def main() -> None:
    user_code_file = sys.argv[1]   # 用户代码文件路径
    paths_file = sys.argv[2]       # 表路径映射 JSON 文件

    # 读取表路径映射, 提供给生成代码
    with open(paths_file, encoding="utf-8") as fh:
        table_paths = json.load(fh)
    table_names = list(table_paths.keys())

    # 读取用户代码
    with open(user_code_file, encoding="utf-8") as fh:
        user_code = fh.read()

    # 供用户代码使用的工作命名空间
    sandbox_globals = {
        "__builtins__": _BUILTINS,
        "table_paths": table_paths,
        "table_names": table_names,
    }

    try:
        # 编译并真正执行
        exec(compile(user_code, "<generated>", "exec"), sandbox_globals)
        result = sandbox_globals.get("result", [])
        if not isinstance(result, list):
            result = []
        # 打印结果标记供主进程回收（ensure_ascii 保证输出为纯 ASCII 字节流）
        sys.stdout.write("__RESULT__" + json.dumps({"result": result}, default=str, ensure_ascii=True))
    except Exception as exc:  # 用户代码的任何异常都输出到 stderr 供反思使用
        sys.stderr.write(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
