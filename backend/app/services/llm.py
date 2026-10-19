"""LLM 接入层：统一抽象接口。

实现方案：
- OpenAICompatibleProvider：通过 OpenAI 兼容的 chat/completions 接口对接
  DeepSeek / Qwen(DashScope) / Ollama 等，只需更换 base_url 与模型名。
- MockProvider：无 API Key 时保底可用，返回固定占位内容。

配置入口(app.core.config)：
    LLM_PROVIDER = "api" | "mock"
    LLM_API_BASE、LLM_API_KEY、LLM_MODEL
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import httpx

from app.core.config import settings

# 系统提示词：约束模型扮演数据分析 Agent, 只输出 JSON
SYSTEM_PROMPT = (
    "你是一个专业的企业数据分析 Agent。你会收到用户问题与表格的 Schema 画像。\n"
    "你只负责输出 JSON 结构，不要输出任何 Markdown 代码块标记或额外解释。\n"
    "所有输出必须是合法 JSON 字符串。"
)


class LLMProvider(ABC):
    """任意大模型接入需实现的最简接口。"""

    @abstractmethod
    def plan(self, question: str, context: str) -> List[str]:
        """根据用户问题与 Schema 画像, 输出分析计划步骤。"""

    @abstractmethod
    def generate_code(self, question: str, context: str, plan: List[str]) -> str:
        """按计划生成可执行的 DuckDB/pandas 代码。"""

    @abstractmethod
    def fix_code(self, question: str, context: str, code: str, error: str) -> str:
        """根据执行报错反思, 修正候选代码。"""

    @abstractmethod
    def write_conclusion(self, question: str, output: List[dict]) -> str:
        """根据执行结果摘要撰写结论。"""

    def complete_followup(self, question: str, last_question: str, last_conclusion: str, context: str) -> str:
        """把极简追问补全为完整、自包含的问题。

        默认实现直接返回原问题（供不使用全局上下文的场景）；真实模型会结合
        上一轮问题/结论与数据画像补全，例如"一月呢"→"华东地区一月销售额是多少"。
        """
        return question


class OpenAICompatibleProvider(LLMProvider):
    """通过 OpenAI 兼容接口对接任意兼容服务（DeepSeek/Qwen/Ollama）。"""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        # 单例 httpx 客户端
        self._client = httpx.Client(timeout=60.0)

    def _chat(self, prompt: str) -> str:
        """调用一次 chat/completions, 返回 assistant 的纯文本回复。"""
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,   # 低温度保证 SQL/代码生成稳定
        }
        resp = self._client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """从模型回复中稳健地提取 JSON 对象。"""
        # 去掉可能的 Markdown 代码围栏
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1)
        # 去掉前三行与末尾的空行后尝试解析
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 从首个 '{' 到末尾的 '}' 提取再解析
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end + 1])
            raise ValueError(f"无法从模型回复解析 JSON: {text[:200]}")

    def plan(self, question: str, context: str) -> List[str]:
        prompt = (
            f"【用户问题】\n{question}\n\n"
            f"【表格 Schema 画像】\n{context}\n\n"
            "请给出一个分析计划，用 JSON 数组输出，每个元素是一步简短明确的动作。"
            "示例：[\"按区域聚合销售额\", \"计算环比\", \"定位异常区域\"]。"
            '只输出形如 {"plan": [...]} 的 JSON。'
        )
        data = self._extract_json(self._chat(prompt))
        plan = data.get("plan") or []
        return [str(p) for p in plan]

    def generate_code(self, question: str, context: str, plan: List[str], base_code: str = "") -> str:
        base_section = ""
        if base_code:
            # 这是追问场景：要求基于上一轮代码修改条件，保证逻辑延续、数值真实
            base_section = (
                "【这是对上一轮分析的追问/假设检验】\n"
                "请在下面这段‘上一轮代码’的基础上，按当前问题调整条件后重新计算，\n"
                "不要从头全新重写整段逻辑，保留读取与聚合结构，只改查询条件/过滤/聚合。\n"
                "确保最终仍把结果放入变量 result（list[dict]）。\n"
                "上一轮代码：\n```\n"
                + base_code +
                "\n```\n"
            )
        prompt = (
            f"【用户问题】\n{question}\n\n"
            f"【表格 Schema 画像】\n{context}\n\n"
            f"【分析计划】\n{json.dumps(plan, ensure_ascii=False)}\n\n"
            + base_section +
            "请生成一段 Python 代码实现上述分析，结果数据必须放入变量 result（list[dict]）。\n"
            "【数据读取样板】（每条表都要读文件）\n"
            "    import pandas as pd\n"
            "    df1 = pd.read_csv(table_paths['表ID']) if str(table_paths['表ID']).endswith('.csv') else pd.read_excel(table_paths['表ID'])\n"
            "【推荐写法】优先使用 pandas 完成聚合/统计，例如：\n"
            "    out = df1.groupby('region')['sales'].sum().reset_index().sort_values('sales', ascending=False)\n"
            "    result = out.to_dict('records')\n"
            "【注意】如果你用 duckdb.query(...)，DuckDB 无法直接查询 pandas DataFrame 变量；\n"
            "    必须先 con = duckdb.connect(); con.register('t', df1); 再 con.execute('...').df()。\n"
            "严禁访问网络、读写文件系统、import 白名单以外的库。\n"
            '只输出形如 {"code": "..."} 的 JSON，code 为纯 Python 代码。'
        )
        data = self._extract_json(self._chat(prompt))
        return data.get("code") or ""

    def fix_code(self, question: str, context: str, code: str, error: str) -> str:
        prompt = (
            f"【用户问题】\n{question}\n\n"
            f"【表格 Schema 画像】\n{context}\n\n"
            "【上一次生成的代码】\n"
            f"{code}\n\n"
            f"【执行报错】\n{error}\n\n"
            "请修正这段代码使其能正确运行并得到结果。\n"
            "【关键纠错点】\n"
            "1) duckdb.query 不能直接查询 pandas DataFrame 变量，必须 con.register('名', df) 注册后才能查；\n"
            "   或改用纯 pandas groupby 聚合；\n"
            "2) 确保所有引用的变量都已在代码中定义；\n"
            "3) 读取文件用 table_paths['表ID']（.csv→pd.read_csv，.xlsx→pd.read_excel）；\n"
            "4) 最终结果放入变量 result（list[dict]）。\n"
            '只输出形如 {"code": "..."} 的 JSON。'
        )
        data = self._extract_json(self._chat(prompt))
        return data.get("code") or code

    def complete_followup(self, question: str, last_question: str, last_conclusion: str, context: str) -> str:
        """把极简追问补全为完整、自包含的问题，避免 LLM 因语义缺失而编造数据。

        结合上一轮问题、上一轮结论与数据画像，补齐"一月呢"这类省略句式中的
        地点/时间/聚合维度等信息。
        """
        prompt = (
            "你正在维护一段连续的数据分析对话。用户当前是一个很简短的追问，"
            "它省略了大量上下文。请结合上一轮的问题、结论和可用数据的表结构，"
            "把这个追问补全成一句**完整、自包含、表意清晰**的分析问题，"
            "使得仅凭这一句就能准确执行查询。\n\n"
            f"【上一轮问题】\n{last_question}\n\n"
            f"【上一轮结论】\n{last_conclusion}\n\n"
            f"【可用数据表结构】\n{context}\n\n"
            f"【用户本次追问（极简）】\n{question}\n\n"
            "要求：\n"
            "1) 补全后必须保留用户真正想改变的点（如把2月换成1月）；\n"
            "2) 补全后必须自包含：包含明确的主体、维度、指标与限定条件；\n"
            "3) 不要凭空发明数据中不存在的字段/值，只能用表结构里的列与上一轮提到的内容；\n"
            "4) 若追问与上一轮完全无关，就原样保留用户问题。\n"
            '只输出形如 {"question": "补全后的问题"} 的 JSON。'
        )
        data = self._extract_json(self._chat(prompt))
        # 兼容键名可能被模型写成不同形式
        completed = data.get("question") or data.get("completed_question") or question
        return str(completed)

    def _write_conclusion_prompt(self, question: str, output: List[dict], chart_json: str = "") -> str:
        return (
            f"【用户问题】\n{question}\n\n"
            f"【分析结果数据】\n{json.dumps(output, ensure_ascii=False, default=str)[:4000]}\n\n"
            f"【图表配置】\n{chart_json}\n\n"
            "请写一段简洁的中文分析结论（3~6 句），说明主要发现、趋势或异常，并给出可执行的建议。"
            '只输出形如 {"conclusion": "..."} 的 JSON。'
        )

    def write_conclusion(self, question: str, output: List[dict]) -> str:
        data = self._extract_json(self._chat(self._write_conclusion_prompt(question, output)))
        return data.get("conclusion") or ""

    def write_conclusion_with_chart(self, question: str, output: List[dict], chart_json: str) -> str:
        """在拿到图表配置后再生成更贴合图表的结论。"""
        data = self._extract_json(self._chat(self._write_conclusion_prompt(question, output, chart_json)))
        return data.get("conclusion") or ""


class MockProvider(LLMProvider):
    """保底实现：不调用真实模型, 返回固定内容以保证链路可跑通。"""

    def plan(self, question: str, context: str) -> List[str]:
        return ["加载相关表格", f"按问题执行聚合指标: {question[:30]}", "汇总并生成结论"]

    def generate_code(self, question: str, context: str, plan: List[str], base_code: str = "") -> str:
        # 返回一段可成功执行的占位代码：对每张表读入并输出行数
        lines = [
            "import pandas as pd",
            "output = []",
            "for tid, path in table_paths.items():",
            "    df = pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)",
            "    output.append({'table': tid, 'rows': len(df), 'columns': len(df.columns)})",
            "result = output",
        ]
        return "\n".join(lines)

    def fix_code(self, question: str, context: str, code: str, error: str) -> str:
        return code

    def write_conclusion(self, question: str, output: List[dict]) -> str:
        return f"[占位结论] 已针对问题『{question}』完成分析，输出行数：{len(output) if output else 0}。"


def get_llm() -> LLMProvider:
    """根据配置返回对应 LLM Provider。"""
    if settings.LLM_PROVIDER == "api":
        if not settings.LLM_API_KEY or settings.LLM_API_KEY.startswith("sk-你的"):
            raise RuntimeError(
                "LLM_PROVIDER=api 但未配置有效的 LLM_API_KEY。"
                "请复制 backend/.env.example 为 backend/.env 并填入 DeepSeek API Key。"
            )
        return OpenAICompatibleProvider(
            base_url=settings.LLM_API_BASE,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
        )
    if settings.LLM_PROVIDER == "ollama":
        # Ollama 本地模型：无需 API Key
        return OpenAICompatibleProvider(
            base_url=settings.OLLAMA_BASE_URL + "/v1",
            api_key="",
            model=settings.LLM_MODEL,
        )
    return MockProvider()
