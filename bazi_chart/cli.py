#!/usr/bin/env python3
"""
CLI for BaziChart — 八字排盘命令行工具

Usage:
    python -m bazi_chart.cli 1984 6 15 8          # Basic chart
    python -m bazi_chart.cli 1984 6 15 8 --json   # JSON output
    python -m bazi_chart.cli 1984 6 15 8 --analyze career  # AI analysis
    python -m bazi_chart.cli 1984 6 15 8 --mock   # Mock analysis demo
"""

import argparse
import json
import sys

from .core import compute_chart
from .ai_stub import analyze_chart, create_analyzer, PROMPT_TEMPLATES


def main():
    parser = argparse.ArgumentParser(
        description="BaziChart — 八字排盘工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1984 6 15 8              排盘显示
  %(prog)s 1984 6 15 8 --json       输出JSON
  %(prog)s 1984 6 15 8 --mock       模拟AI解读
  %(prog)s 1984 6 15 8 --analyze career  职业分析（需API key）
        """,
    )
    parser.add_argument("year", type=int, help="出生年份 (Gregorian, e.g. 1984)")
    parser.add_argument("month", type=int, help="出生月份 (1-12)")
    parser.add_argument("day", type=int, help="出生日期 (1-31)")
    parser.add_argument("hour", type=int, nargs="?", default=0, help="出生时辰 (0-23), 默认 0")
    parser.add_argument("--minute", type=int, default=0, help="出生分钟 (0-59), 默认 0")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--analyze", type=str, nargs="?", const="general",
                        choices=list(PROMPT_TEMPLATES.keys()),
                        help=f"AI 分析模板: {', '.join(PROMPT_TEMPLATES.keys())}")
    parser.add_argument("--mock", action="store_true", help="使用 Mock 模式（无需 API key）")
    
    args = parser.parse_args()
    
    # Compute chart
    try:
        chart = compute_chart(args.year, args.month, args.day, args.hour, args.minute)
    except Exception as e:
        print(f"排盘失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output
    if args.json:
        print(json.dumps(chart.to_dict(), ensure_ascii=False, indent=2))
    elif args.analyze or args.mock:
        use_mock = args.mock or not args.analyze
        template = args.analyze or "general"
        analyzer = create_analyzer(use_mock=use_mock)
        result = analyze_chart(chart, template, analyzer)
        print(chart.display())
        print()
        print("─" * 50)
        print(f"  AI 解读 [{template}]:")
        print("─" * 50)
        print(result)
    else:
        print(chart.display())


if __name__ == "__main__":
    main()
