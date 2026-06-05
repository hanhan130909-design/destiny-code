"""
BaziChart — 八字排盘核心算法模块
"""
__version__ = "0.1.0"

# Graceful imports — don't fail on missing optional modules
try:
    from .core import BaziChart, Pillar, compute_chart
except ImportError:
    pass

try:
    from .ai_stub import (
        BaseAnalyzer, OpenAIAnalyzer, MockAnalyzer,
        analyze_chart, create_analyzer, PROMPT_TEMPLATES,
    )
except ImportError:
    pass

try:
    from .constants import (
        TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING,
        NAYIN, SOLAR_TERMS, SHENGXIAO,
    )
except ImportError:
    pass

try:
    from .github_db import read_submissions, append_submission, read_followups, save_followups
except ImportError:
    pass
