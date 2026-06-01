"""
BaziChart core calculation module.

Computes the Four Pillars (四柱) from a Gregorian birth date and time:
  - Year Pillar (年柱): Heavenly Stem + Earthly Branch
  - Month Pillar (月柱): Heavenly Stem + Earthly Branch
  - Day Pillar (日柱): Heavenly Stem + Earthly Branch
  - Hour Pillar (时柱): Heavenly Stem + Earthly Branch

Also computes: Nayin (纳音), Hidden Stems (藏干), Ten Gods (十神), Five Elements,
Yin/Yang, Zodiac, and Empty Branches (空亡).
"""

import datetime
from dataclasses import dataclass, field
from typing import Optional

from .constants import (
    TIANGAN, TIANGAN_PINYIN, TIANGAN_WUXING, TIANGAN_YINYANG,
    DIZHI, DIZHI_PINYIN, DIZHI_WUXING, DIZHI_YINYANG,
    SHENGXIAO, HOUR_TO_DIZHI, SOLAR_TERMS, SOLAR_TERM_NAMES,
    NAYIN, HIDDEN_STEMS, WUHU_MONTH_STEM, WUSHU_HOUR_STEM,
    SHISHEN_TABLE, SHISHEN_NAMES, nayin_index,
)


# ── Helper: days from a reference date ────────────────────────────────

def _days_between(d1: datetime.date, d2: datetime.date) -> int:
    """Return number of days d2 - d1."""
    return (d2 - d1).days


# ── Year Pillar ───────────────────────────────────────────────────────

def _is_before_lichun(year: int, month: int, day: int) -> bool:
    """Check if date is before 立春 of the given year."""
    terms = SOLAR_TERMS.get(year)
    if not terms:
        return False
    _, lc_m, lc_d = terms[0]  # (year, month, day)
    if month < lc_m:
        return True
    if month == lc_m and day < lc_d:
        return True
    return False


def year_pillar(year: int, month: int, day: int) -> tuple[int, int]:
    """
    Compute year pillar (天干index, 地支index) for a Gregorian date.
    
    The sexagenary year begins at 立春, not Jan 1 or Lunar New Year.
    Returns (stem_index, branch_index) both 1-indexed.
    """
    if _is_before_lichun(year, month, day):
        year -= 1  # Use previous sexagenary year
    
    # Stem: (year - 4) % 10 → 1-indexed
    stem = ((year - 4) % 10) + 1
    # Branch: (year - 4) % 12 → 1-indexed
    branch = ((year - 4) % 12) + 1
    
    return (stem, branch)


# ── Month Pillar ──────────────────────────────────────────────────────

# Jie indices (节, month boundaries) in the 24 solar terms
_JIE_INDICES = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
# Corresponding earthly branches for each month period
_JIE_BRANCHES = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2]  # 寅..丑


def _find_month_branch(year: int, month: int, day: int) -> int:
    """
    Determine the month earthly branch based on which solar term interval
    the date falls into. Returns branch index (1-12).
    
    Month boundaries are the 12 Jie (节):
      寅月: 立春→惊蛰   卯月: 惊蛰→清明   辰月: 清明→立夏
      巳月: 立夏→芒种   午月: 芒种→小暑   未月: 小暑→立秋
      申月: 立秋→白露   酉月: 白露→寒露   戌月: 寒露→立冬
      亥月: 立冬→大雪   子月: 大雪→小寒   丑月: 小寒→立春
    
    Solar terms are stored as (year, month, day) so year-boundary
    intervals (子月 and 丑月) are handled naturally.
    """
    import datetime
    
    terms = SOLAR_TERMS.get(year)
    if not terms:
        return ((month + 1) % 12) or 12
    
    birth = datetime.date(year, month, day)
    
    # Build all jie intervals that could contain this date.
    # Include previous year's last two jie intervals (子月, 丑月)
    # which may reach into January of this year.
    intervals = []
    
    # Previous year's 大雪→小寒 (子月) and 小寒→立春 (丑月)
    prev_terms = SOLAR_TERMS.get(year - 1)
    if prev_terms:
        # 大雪→小寒: 子月
        dy, dm, dd = prev_terms[20]
        xy, xm, xd = prev_terms[22]
        intervals.append((datetime.date(dy, dm, dd), datetime.date(xy, xm, xd), 1))
        # 小寒→立春: 丑月
        lcy, lcm, lcd = terms[0]
        intervals.append((datetime.date(xy, xm, xd), datetime.date(lcy, lcm, lcd), 2))
    
    # Current year's jie intervals (立春 through 大雪→小寒 of next year)
    for i, ji in enumerate(_JIE_INDICES):
        sy, sm, sd = terms[ji]
        start = datetime.date(sy, sm, sd)
        
        next_ji = _JIE_INDICES[(i + 1) % 12]
        ey, em, ed = terms[next_ji]
        end = datetime.date(ey, em, ed)
        
        intervals.append((start, end, _JIE_BRANCHES[i]))
    
    # Find which interval contains the birth date
    for start, end, branch in intervals:
        if start <= birth < end:
            return branch
    
    # Fallback
    return ((month + 1) % 12) or 12


def month_pillar(year_stem: int, year: int, month: int, day: int) -> tuple[int, int]:
    """
    Compute month pillar (天干index, 地支index).
    
    Uses 五虎遁 (Five Tigers Escape) to derive month stem from year stem.
    Returns (stem_index, branch_index) both 1-indexed.
    """
    branch = _find_month_branch(year, month, day)
    
    # Determine month stem from year stem via 五虎遁
    # Map year stem to 五虎遁 group: 甲己→1, 乙庚→2, 丙辛→3, 丁壬→4, 戊癸→5
    group_stems = {1: 1, 6: 1, 2: 2, 7: 2, 3: 3, 8: 3, 4: 4, 9: 4, 5: 5, 10: 5}
    group = group_stems.get(year_stem, 1)
    
    stem = WUHU_MONTH_STEM.get(group, {}).get(branch, 1)
    
    return (stem, branch)


# ── Day Pillar ────────────────────────────────────────────────────────

# Reference: 1900-01-01 = 甲戌日 (stem=1, branch=11)
_REF_DATE = datetime.date(1900, 1, 1)
_REF_STEM = 1   # 甲
_REF_BRANCH = 11  # 戌


def day_pillar(year: int, month: int, day: int) -> tuple[int, int]:
    """
    Compute day pillar (天干index, 地支index).
    
    Uses day count from reference date 1900-01-01 (甲戌日), modulo 60.
    Returns (stem_index, branch_index) both 1-indexed.
    """
    d = datetime.date(year, month, day)
    delta = _days_between(_REF_DATE, d)
    
    # Stem: 10-day cycle
    stem = ((_REF_STEM - 1 + delta) % 10) + 1
    # Branch: 12-day cycle
    branch = ((_REF_BRANCH - 1 + delta) % 12) + 1
    
    return (stem, branch)


# ── Hour Pillar ───────────────────────────────────────────────────────

def hour_pillar(day_stem: int, hour: int) -> tuple[int, int]:
    """
    Compute hour pillar (天干index, 地支index).
    
    Hour branch is determined by the two-hour period (时辰).
    Hour stem is derived from day stem via 五鼠遁 (Five Rats Escape).
    Returns (stem_index, branch_index) both 1-indexed.
    """
    # Get hour branch
    branch = HOUR_TO_DIZHI[hour % 24][1]
    
    # Map day stem to 五鼠遁 group: 甲己→1, 乙庚→2, 丙辛→3, 丁壬→4, 戊癸→5
    group_stems = {1: 1, 6: 1, 2: 2, 7: 2, 3: 3, 8: 3, 4: 4, 9: 4, 5: 5, 10: 5}
    group = group_stems.get(day_stem, 1)
    
    stem = WUSHU_HOUR_STEM.get(group, {}).get(branch, 1)
    
    return (stem, branch)


# ── Pillar dataclass ──────────────────────────────────────────────────

@dataclass
class Pillar:
    """A single pillar (柱) with stem and branch."""
    stem: int          # 1-10
    branch: int        # 1-12
    stem_name: str = ""
    branch_name: str = ""
    stem_pinyin: str = ""
    branch_pinyin: str = ""
    stem_wuxing: str = ""
    branch_wuxing: str = ""
    stem_yinyang: str = ""
    branch_yinyang: str = ""
    nayin: str = ""
    hidden_stems: list = field(default_factory=list)
    zodiac: str = ""
    pillar_type: str = ""  # "年", "月", "日", "时"

    def __post_init__(self):
        if not self.stem_name:
            self.stem_name = TIANGAN[self.stem]
        if not self.branch_name:
            self.branch_name = DIZHI[self.branch]
        if not self.stem_pinyin:
            self.stem_pinyin = TIANGAN_PINYIN[self.stem]
        if not self.branch_pinyin:
            self.branch_pinyin = DIZHI_PINYIN[self.branch]
        if not self.stem_wuxing:
            self.stem_wuxing = TIANGAN_WUXING[self.stem]
        if not self.branch_wuxing:
            self.branch_wuxing = DIZHI_WUXING[self.branch]
        if not self.stem_yinyang:
            self.stem_yinyang = TIANGAN_YINYANG[self.stem]
        if not self.branch_yinyang:
            self.branch_yinyang = DIZHI_YINYANG[self.branch]
        if not self.nayin:
            self.nayin = NAYIN[nayin_index(self.stem, self.branch)]
        if not self.hidden_stems:
            self.hidden_stems = [
                {"stem": TIANGAN[s], "pinyin": TIANGAN_PINYIN[s], "wuxing": TIANGAN_WUXING[s], "level": lvl}
                for s, lvl in HIDDEN_STEMS.get(self.branch, [])
            ]
        if not self.zodiac and self.pillar_type == "年":
            self.zodiac = SHENGXIAO[self.branch]

    def __str__(self):
        return f"{self.stem_name}{self.branch_name}"

    def to_dict(self) -> dict:
        return {
            "stem": self.stem,
            "branch": self.branch,
            "stem_name": self.stem_name,
            "branch_name": self.branch_name,
            "stem_pinyin": self.stem_pinyin,
            "branch_pinyin": self.branch_pinyin,
            "stem_wuxing": self.stem_wuxing,
            "branch_wuxing": self.branch_wuxing,
            "stem_yinyang": self.stem_yinyang,
            "branch_yinyang": self.branch_yinyang,
            "ganzhi": str(self),
            "nayin": self.nayin,
            "hidden_stems": self.hidden_stems,
            "zodiac": self.zodiac,
            "type": self.pillar_type,
        }


# ── Ten Gods (十神) computation ───────────────────────────────────────

def compute_shishen(day_stem: int, other_stem: int) -> str:
    """
    Compute the Ten Gods (十神) relationship between the day stem and another stem.
    
    Args:
        day_stem: Day master stem index (1-10)
        other_stem: Other stem index whose relationship to day master is computed
    
    Returns:
        Name of the Ten God relationship (e.g., "正官", "食神", etc.)
    """
    idx = SHISHEN_TABLE.get(day_stem, {}).get(other_stem, 0)
    return SHISHEN_NAMES[idx]


# ── Empty Branches (空亡) ─────────────────────────────────────────────

def compute_xunkong(day_stem: int, day_branch: int) -> tuple[int, int]:
    """
    Compute the two empty (void) branches (空亡) for a given day pillar.
    
    The sexagenary cycle is divided into 6旬 (10-day periods).
    Each 旬 has 2 missing branches = 空亡.
    
    Returns (branch1, branch2) both 1-indexed.
    """
    # Which 旬 (0-5) does this day pillar belong to?
    # 甲子旬: 甲子→癸酉, empty: 戌亥 (11, 12)
    # 甲戌旬: 甲戌→癸未, empty: 申酉 (9, 10)
    # 甲申旬: 甲申→癸巳, empty: 午未 (7, 8)
    # 甲午旬: 甲午→癸卯, empty: 辰巳 (5, 6)
    # 甲辰旬: 甲辰→癸丑, empty: 寅卯 (3, 4)
    # 甲寅旬: 甲寅→癸亥, empty: 子丑 (1, 2)
    
    # Calculate position in cycle: (stem-1)*6 + (branch-1) → position 0-59
    # But easier: find which 甲 day starts the旬
    # 旬_start_stem = 1 (甲), 旬_start_branch cycles through all 12
    # We find the 甲 day at or before current day
    
    # Position of 甲 in the旬: the 甲 is at branch_index where branch matches stem
    # 甲子(1,1), 甲戌(1,11), 甲申(1,9), 甲午(1,7), 甲辰(1,5), 甲寅(1,3)
    xun_starts = {1:1, 11:2, 9:3, 7:4, 5:5, 3:6}
    
    # Find the旬 start branch — the 甲 day whose branch is at or before current branch
    # Go backwards from current day_branch to find the nearest 甲 branch
    for offset in range(6):
        check_branch = ((day_branch - 1 - offset) % 12) + 1
        if check_branch in xun_starts:
            xun_num = xun_starts[check_branch]
            break
    
    # 空亡 mapping
    xunkong_map = {
        1: (11, 12),  # 甲子旬 → 戌亥
        2: (9, 10),   # 甲戌旬 → 申酉
        3: (7, 8),    # 甲申旬 → 午未
        4: (5, 6),    # 甲午旬 → 辰巳
        5: (3, 4),    # 甲辰旬 → 寅卯
        6: (1, 2),    # 甲寅旬 → 子丑
    }
    
    return xunkong_map[xun_num]


# ── Full BaziChart ────────────────────────────────────────────────────

@dataclass
class BaziChart:
    """
    Complete Bazi (八字) chart with all four pillars and computed relationships.
    """
    birth_date: datetime.date
    birth_hour: int  # 0-23
    
    year_pillar: Optional[Pillar] = None
    month_pillar: Optional[Pillar] = None
    day_pillar: Optional[Pillar] = None
    hour_pillar: Optional[Pillar] = None
    
    day_master: str = ""        # 日主 (the day stem)
    day_master_wuxing: str = "" # Day master's five element
    day_master_yinyang: str = ""# Day master's yin/yang
    
    shishen: dict = field(default_factory=dict)  # pillar_type → shishen name
    xunkong: list = field(default_factory=list)  # list of empty branch names
    
    def compute(self):
        """Compute all four pillars and derived attributes."""
        y, m, d = self.birth_date.year, self.birth_date.month, self.birth_date.day
        
        # Year pillar
        ys, yb = year_pillar(y, m, d)
        self.year_pillar = Pillar(stem=ys, branch=yb, pillar_type="年")
        
        # Month pillar
        ms, mb = month_pillar(ys, y, m, d)
        self.month_pillar = Pillar(stem=ms, branch=mb, pillar_type="月")
        
        # Day pillar
        ds, db = day_pillar(y, m, d)
        self.day_pillar = Pillar(stem=ds, branch=db, pillar_type="日")
        
        # Hour pillar
        hs, hb = hour_pillar(ds, self.birth_hour)
        self.hour_pillar = Pillar(stem=hs, branch=hb, pillar_type="时")
        
        # Day master
        self.day_master = TIANGAN[ds]
        self.day_master_wuxing = TIANGAN_WUXING[ds]
        self.day_master_yinyang = TIANGAN_YINYANG[ds]
        
        # Ten Gods for each pillar's stem relative to day master
        self.shishen = {
            "年": compute_shishen(ds, ys),
            "月": compute_shishen(ds, ms),
            "日": "日主",  # Day pillar stem is the master itself
            "时": compute_shishen(ds, hs),
        }
        # Also compute shishen for hidden stems in day branch
        self.shishen_hidden = {}
        for hs_data in self.day_pillar.hidden_stems:
            hs_idx = TIANGAN.index(hs_data["stem"])
            self.shishen_hidden[hs_data["stem"]] = compute_shishen(ds, hs_idx)
        
        # Empty branches (空亡)
        xk1, xk2 = compute_xunkong(ds, db)
        self.xunkong = [
            {"index": xk1, "name": DIZHI[xk1], "pinyin": DIZHI_PINYIN[xk1]},
            {"index": xk2, "name": DIZHI[xk2], "pinyin": DIZHI_PINYIN[xk2]},
        ]
        
        return self
    
    def to_dict(self) -> dict:
        """Export chart as a dictionary."""
        return {
            "birth": {
                "date": str(self.birth_date),
                "hour": self.birth_hour,
            },
            "pillars": {
                "year": self.year_pillar.to_dict() if self.year_pillar else None,
                "month": self.month_pillar.to_dict() if self.month_pillar else None,
                "day": self.day_pillar.to_dict() if self.day_pillar else None,
                "hour": self.hour_pillar.to_dict() if self.hour_pillar else None,
            },
            "day_master": {
                "stem": self.day_master,
                "wuxing": self.day_master_wuxing,
                "yinyang": self.day_master_yinyang,
            },
            "shishen": self.shishen,
            "xunkong": self.xunkong,
        }
    
    def display(self) -> str:
        """Human-readable chart display."""
        p = self
        yp, mp, dp, hp = p.year_pillar, p.month_pillar, p.day_pillar, p.hour_pillar
        lines = [
            f"{'='*50}",
            f"  Bazi Chart — {p.birth_date} {p.birth_hour:02d}:00",
            f"{'='*50}",
            f"",
            f"  Year:  {yp}  纳音: {yp.nayin}  生肖: {yp.zodiac}",
            f"  Month: {mp}  纳音: {mp.nayin}",
            f"  Day:   {dp}  纳音: {dp.nayin}  ← 日主 ({p.day_master}, {p.day_master_wuxing}{p.day_master_yinyang})",
            f"  Hour:  {hp}  纳音: {hp.nayin}",
            f"",
            f"  Ten Gods (十神):",
            f"    年: {p.shishen['年']}  月: {p.shishen['月']}  日: {p.shishen['日']}  时: {p.shishen['时']}",
            f"",
            f"  Hidden Stems (藏干) in Day Branch:",
        ]
        for hs in dp.hidden_stems:
            lines.append(f"    {hs['stem']}({hs['wuxing']}) — {hs['level']}气")
        
        lines.append(f"")
        lines.append(f"  Empty Branches (空亡): {DIZHI[p.xunkong[0]['index']]}, {DIZHI[p.xunkong[1]['index']]}")
        lines.append(f"{'='*50}")
        
        return "\n".join(lines)


# ── Convenience function ──────────────────────────────────────────────

def compute_chart(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> BaziChart:
    """
    Compute a full Bazi chart from Gregorian birth date and time.
    
    Args:
        year: Gregorian year (e.g., 1984)
        month: Month (1-12)
        day: Day (1-31)
        hour: Hour (0-23)
        minute: Minute (0-59) — currently unused, reserves for future accuracy
    
    Returns:
        BaziChart with all pillars computed.
    """
    chart = BaziChart(
        birth_date=datetime.date(year, month, day),
        birth_hour=hour,
    )
    chart.compute()
    return chart
