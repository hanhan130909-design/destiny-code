"""
BaziChart — 八字排盘核心算法模块

Usage:
    from bazi_chart import compute_chart, analyze_chart
    
    chart = compute_chart(1984, 6, 15, 8)
    print(chart.display())
"""

from .core import BaziChart, Pillar, compute_chart
from .ai_stub import (
    BaseAnalyzer,
    OpenAIAnalyzer,
    MockAnalyzer,
    analyze_chart,
    create_analyzer,
    PROMPT_TEMPLATES,
)
from .constants import (
    TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING,
    NAYIN, SOLAR_TERMS, SHENGXIAO,
)

__version__ = "0.1.0"
__all__ = [
    "BaziChart", "Pillar", "compute_chart",
    "BaseAnalyzer", "OpenAIAnalyzer", "MockAnalyzer",
    "analyze_chart", "create_analyzer", "PROMPT_TEMPLATES",
    "TIANGAN", "DIZHI", "TIANGAN_WUXING", "DIZHI_WUXING",
    "NAYIN", "SOLAR_TERMS", "SHENGXIAO",
]
