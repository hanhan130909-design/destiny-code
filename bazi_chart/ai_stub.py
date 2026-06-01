"""
AI integration stubs for BaziChart analysis and interpretation.

Reserved OpenAI-compatible API interface. Currently stubbed;
swap in a real API key and model to enable AI-powered readings.

Architecture:
  - BaseAnalyzer: abstract interface for chart analysis
  - OpenAIAnalyzer: OpenAI-compatible implementation (stubbed)
  - MockAnalyzer: returns template-based responses for testing
  - analyze_chart(): convenience function
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Callable

from .core import BaziChart


# ── Base Analyzer Interface ───────────────────────────────────────────

class BaseAnalyzer(ABC):
    """Abstract base for Bazi chart analyzers."""

    @abstractmethod
    def analyze(self, chart: BaziChart, prompt_template: str = "general") -> str:
        """
        Analyze a Bazi chart and return interpretation text.
        
        Args:
            chart: Computed BaziChart
            prompt_template: Named prompt template to use
        
        Returns:
            Analysis text
        """
        ...

    @abstractmethod
    def chat(self, chart: BaziChart, message: str) -> str:
        """
        Interactive chat about a chart.
        
        Args:
            chart: Computed BaziChart
            message: User's follow-up question
        
        Returns:
            Response text
        """
        ...


# ── Prompt Templates ──────────────────────────────────────────────────

PROMPT_TEMPLATES = {
    "general": """
你是一位精通八字命理的专家。请根据以下八字排盘进行综合分析。

{chart_data}

请从以下方面进行解读：
1. 日主强弱分析
2. 五行喜忌
3. 性格特征
4. 事业财运
5. 感情婚姻
6. 健康注意
7. 大运走势简述

请用中文回答，专业但不晦涩，条理清晰。
""",

    "career": """
你是一位精通八字命理的职业规划专家。请分析以下八字的职业发展方向。

{chart_data}

请重点分析：
1. 适合的行业和职业类型
2. 事业发展关键时间点
3. 贵人运和合作伙伴特质
4. 财运趋势

请用中文回答。
""",

    "relationship": """
你是一位精通八字命理的感情婚姻专家。请分析以下八字的感情婚姻状况。

{chart_data}

请重点分析：
1. 配偶星和配偶宫
2. 感情运势
3. 适合的伴侣类型
4. 婚姻注意事项

请用中文回答。
""",

    "health": """
你是一位精通八字命理的健康养生专家。请分析以下八字的健康状况。

{chart_data}

请重点分析：
1. 五行平衡与健康
2. 易患疾病倾向
3. 养生建议
4. 关键年龄注意事项

请用中文回答。
""",

    "yearly": """
你是一位精通八字命理的流年运势专家。请分析以下八字的当年运势。

{chart_data}

请重点分析：
1. 今年总体运势
2. 事业运
3. 财运
4. 感情运
5. 健康运
6. 每月关键节点

请用中文回答。
""",
}


def _format_chart_for_prompt(chart: BaziChart) -> str:
    """Format a BaziChart as structured text for LLM prompts."""
    d = chart.to_dict()
    
    lines = [
        f"出生日期：{d['birth']['date']} {d['birth']['hour']:02d}:00",
        "",
        "四柱八字：",
    ]
    
    for pillar_key, label in [("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")]:
        p = d["pillars"][pillar_key]
        if p:
            lines.append(f"  {label}: {p['ganzhi']} "
                        f"(天干{p['stem_name']}{p['stem_wuxing']}{p['stem_yinyang']}, "
                        f"地支{p['branch_name']}{p['branch_wuxing']}{p['branch_yinyang']}) "
                        f"纳音: {p['nayin']}")
    
    lines.append("")
    lines.append(f"日主：{d['day_master']['stem']} ({d['day_master']['wuxing']}{d['day_master']['yinyang']})")
    
    lines.append("")
    lines.append("十神：")
    lines.append(f"  年: {d['shishen']['年']}  月: {d['shishen']['月']}  日: 日主  时: {d['shishen']['时']}")
    
    lines.append("")
    lines.append(f"空亡：{d['xunkong'][0]['name']}, {d['xunkong'][1]['name']}")
    
    # Hidden stems
    dp = d["pillars"]["day"]
    if dp and dp.get("hidden_stems"):
        lines.append("")
        lines.append("日支藏干：")
        for hs in dp["hidden_stems"]:
            lines.append(f"  {hs['stem']}({hs['wuxing']}) — {hs['level']}气")
    
    return "\n".join(lines)


# ── OpenAI-compatible Analyzer (stubbed) ──────────────────────────────

@dataclass
class OpenAIAnalyzer(BaseAnalyzer):
    """
    OpenAI-compatible API analyzer for Bazi charts.
    
    Currently stubbed — returns a message directing the user to configure
    their API key. When configured, uses the OpenAI chat completions API
    (or any compatible endpoint like vLLM, Ollama, etc.).
    
    Configuration via environment variables:
      OPENAI_API_KEY — API key (required)
      OPENAI_BASE_URL — Base URL (default: https://api.openai.com/v1)
      BAZI_MODEL — Model name (default: gpt-4o)
    """
    
    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    _configured: bool = False
    _chat_history: list = field(default_factory=list)
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")
        if os.environ.get("OPENAI_BASE_URL"):
            self.base_url = os.environ["OPENAI_BASE_URL"]
        if os.environ.get("BAZI_MODEL"):
            self.model = os.environ["BAZI_MODEL"]
        self._configured = bool(self.api_key)
    
    def _stub_response(self) -> str:
        """Return a stub message when API is not configured."""
        return (
            "⚠️ OpenAI API 未配置。\n\n"
            "请设置以下环境变量以启用 AI 分析：\n"
            f"  export OPENAI_API_KEY='sk-...'\n"
            f"  export OPENAI_BASE_URL='{self.base_url}'   # 可选，默认 OpenAI\n"
            f"  export BAZI_MODEL='{self.model}'           # 可选，默认 gpt-4o\n\n"
            "支持任何 OpenAI 兼容 API（vLLM, Ollama, 国产模型等）。\n"
            "配置完成后重新调用即可获得 AI 八字解读。"
        )
    
    def analyze(self, chart: BaziChart, prompt_template: str = "general") -> str:
        """Analyze a chart using the selected prompt template."""
        if not self._configured:
            return self._stub_response()
        
        chart_text = _format_chart_for_prompt(chart)
        template = PROMPT_TEMPLATES.get(prompt_template, PROMPT_TEMPLATES["general"])
        prompt = template.format(chart_data=chart_text)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的八字命理分析师。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except ImportError:
            return self._stub_response() + "\n\n提示: pip install openai"
        except Exception as e:
            return f"API 调用失败: {e}"
    
    def chat(self, chart: BaziChart, message: str) -> str:
        """Continue a conversation about the chart."""
        if not self._configured:
            return self._stub_response()
        
        # Initialize chat history with chart context
        if not self._chat_history:
            chart_text = _format_chart_for_prompt(chart)
            self._chat_history = [
                {"role": "system", "content": "你是一位专业的八字命理分析师。以下是用戶的八字命盤。"},
                {"role": "user", "content": f"我的八字命盤：\n{chart_text}"},
                {"role": "assistant", "content": "已了解您的八字命盤，请随时提问。"},
            ]
        
        self._chat_history.append({"role": "user", "content": message})
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model=self.model,
                messages=self._chat_history,
                temperature=0.7,
                max_tokens=1024,
            )
            reply = response.choices[0].message.content
            self._chat_history.append({"role": "assistant", "content": reply})
            return reply
        except ImportError:
            return self._stub_response() + "\n\n提示: pip install openai"
        except Exception as e:
            return f"API 调用失败: {e}"
    
    def reset_chat(self):
        """Clear chat history."""
        self._chat_history = []


# ── Mock Analyzer (for testing / demo) ────────────────────────────────

class MockAnalyzer(BaseAnalyzer):
    """
    Returns template-based mock responses for testing and demonstration.
    Does not require an API key.
    """
    
    def analyze(self, chart: BaziChart, prompt_template: str = "general") -> str:
        chart_text = _format_chart_for_prompt(chart)
        return (
            f"【Mock 分析 - 未连接 AI】\n\n"
            f"以下是八字排盘数据，可供人工解读：\n\n"
            f"{chart_text}\n\n"
            f"---\n"
            f"提示：配置 OPENAI_API_KEY 环境变量后可获得 AI 智能解读。\n"
            f"支持的分析模板：{', '.join(PROMPT_TEMPLATES.keys())}"
        )
    
    def chat(self, chart: BaziChart, message: str) -> str:
        return (
            f"【Mock 回复】收到问题：「{message}」\n\n"
            f"当前为 Mock 模式。配置 OPENAI_API_KEY 后可使用 AI 对话。"
        )


# ── Convenience ───────────────────────────────────────────────────────

def analyze_chart(
    chart: BaziChart,
    prompt_template: str = "general",
    analyzer: Optional[BaseAnalyzer] = None,
) -> str:
    """
    Convenience function to analyze a Bazi chart.
    
    Args:
        chart: Computed BaziChart
        prompt_template: One of 'general', 'career', 'relationship', 'health', 'yearly'
        analyzer: Optional pre-configured analyzer. If None, auto-detects from env.
    
    Returns:
        Analysis text
    """
    if analyzer is None:
        analyzer = OpenAIAnalyzer()
    return analyzer.analyze(chart, prompt_template)


def create_analyzer(use_mock: bool = False, **kwargs) -> BaseAnalyzer:
    """
    Factory to create an analyzer.
    
    Args:
        use_mock: If True, create a MockAnalyzer (no API needed)
        **kwargs: Passed to OpenAIAnalyzer (model, base_url, api_key)
    
    Returns:
        Configured analyzer
    """
    if use_mock:
        return MockAnalyzer()
    return OpenAIAnalyzer(**kwargs)
