#!/usr/bin/env python3
"""
BaZi Preview Pipeline — Form → Calc → AI → Output

Takes birth data, computes the BaZi chart, derives analysis data
(five-element balance, day master strength, energy theme, etc.),
and produces structured JSON with a formatted preview text.

Phase 1: template-based preview generation (no LLM API required).
Phase 2: wire to OpenAI API for AI-generated previews.

Usage:
    python pipeline.py --year 1984 --month 6 --day 15 --hour 8 --json
    python pipeline.py --year 2000 --month 1 --day 1 --hour 12 --minute 30 --gender F --json
"""

import argparse
import json
import sys
import os
from typing import Optional

# Add parent to path so we can import bazi_chart
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bazi_chart import compute_chart, BaziChart, MockAnalyzer, analyze_chart


# ──────────────────────────────────────────────────────────────────────
# CONSTANTS: Day Master Archetypes (from system prompt v2 + preview v2)
# ──────────────────────────────────────────────────────────────────────

DAY_MASTER_ARCHETYPES = {
    ("甲", "阳"): "the towering tree — pioneer spirit and natural leadership",
    ("乙", "阴"): "the resilient vine — graceful, adaptable, and quietly unstoppable",
    ("丙", "阳"): "the sun itself — radiant, generous, and impossible to ignore",
    ("丁", "阴"): "the candle flame — warm, magnetic, with a light that draws others close",
    ("戊", "阳"): "the mountain — steady, protective, and immovable when it matters",
    ("己", "阴"): "the fertile soil — nurturing, resourceful, the ground where things grow",
    ("庚", "阳"): "the sword — decisive, principled, with a natural instinct for justice",
    ("辛", "阴"): "the jewel — refined, discerning, with an eye for what truly matters",
    ("壬", "阳"): "the ocean — visionary, expansive, carrying depths most never see",
    ("癸", "阴"): "the mist — subtle, intuitive, a quiet wisdom that permeates everything",
}

DAY_MASTER_PERSONALITY = {
    "甲": (
        "You are a bold initiator who thrives on challenge and naturally steps into leadership. "
        "Your forward momentum can be overwhelming — your growth edge lies in learning that true "
        "strength sometimes means pausing so others can catch up."
    ),
    "乙": (
        "You are diplomatic, quietly persistent, and find elegant paths around obstacles that stop "
        "others cold. Your growth edge lies in recognizing when grace becomes avoidance — "
        "sometimes the most elegant path is the direct one."
    ),
    "丙": (
        "You light up a room without trying. Your natural warmth draws people in, and your "
        "enthusiasm is genuinely infectious. Your growth edge lies in learning to sustain your "
        "fire without burning out — the sun doesn't need to shine at full intensity in every "
        "moment to be powerful."
    ),
    "丁": (
        "You carry a steady inner warmth that draws others close — not the blazing sun, but the "
        "candle that illuminates intimate spaces. Your growth edge lies in trusting that your "
        "gentle light is enough — you don't need to burn brighter to matter."
    ),
    "戊": (
        "You are someone others instinctively lean on — reliable, grounded, and immovable when it "
        "counts. Your growth edge lies in learning to bend — the mountain that never shifts can "
        "become isolated from the changing landscape around it."
    ),
    "己": (
        "You are naturally supportive and resourceful — the fertile ground where others' dreams "
        "take root and grow. Your growth edge lies in remembering to nurture yourself with the "
        "same generosity you extend to everyone else."
    ),
    "庚": (
        "You have clear boundaries, a sharp instinct for justice, and a natural decisiveness that "
        "cuts through confusion. Your growth edge lies in softening your delivery — the sword "
        "is most effective when wielded with precision and care, not force."
    ),
    "辛": (
        "You are detail-oriented, refined, and carry high standards that elevate everything you "
        "touch. Your growth edge lies in extending the same grace to yourself that you naturally "
        "offer others — perfectionism can become a cage."
    ),
    "壬": (
        "You are a big-picture thinker, free-spirited and visionary, carrying depths of insight "
        "most people never glimpse. Your growth edge lies in building containers for your vastness "
        "— oceans that never meet the shore remain invisible to the world."
    ),
    "癸": (
        "You are deeply perceptive and emotionally attuned — you sense what others miss and "
        "understand atmospheres with almost psychic precision. Your growth edge lies in protecting "
        "your own energetic boundaries so your sensitivity becomes a gift, not a burden."
    ),
}

# ──────────────────────────────────────────────────────────────────────
# CONSTANTS: Element Fill-in Phrases (from free-preview-v2.md)
# ──────────────────────────────────────────────────────────────────────

ELEMENT_ICONS = {"Wood": "🪵", "Fire": "🔥", "Earth": "🌍", "Metal": "⚙️", "Water": "💧"}

ELEMENT_INSIGHTS = {
    "Wood": {
        0: "Vision and new beginnings are an invitation your chart asks you to consciously cultivate",
        1: "A quiet but persistent capacity for growth and fresh starts",
        2: "A natural balance of vision — you see possibilities without being overwhelmed by them",
        3: "Abundant growth energy — you're a natural initiator with a vision-driven mind",
        4: "A powerful pioneering force — new ideas and expansion are your native language",
    },
    "Fire": {
        0: "Self-expression and passion are an invitation — your chart asks you to kindle your inner spark",
        1: "A precious inner flame — when you express yourself, it matters",
        2: "Warm and naturally expressive — people feel seen and energized around you",
        3: "Radiant presence — you bring warmth, enthusiasm, and charisma to every room",
        4: "A blazing sun — your passion is magnetic and your self-expression is a force",
    },
    "Earth": {
        0: "Stability and grounding are a conscious practice — your growth edge is building inner steadiness",
        1: "A quiet anchor within — you find your footing even in uncertainty",
        2: "Naturally grounded — you create stability that others rely on",
        3: "Deeply stable and nurturing — you're the foundation people build their lives around",
        4: "Mountain-strong — your steadiness and practicality are your superpower",
    },
    "Metal": {
        0: "Discernment and boundaries are an invitation — choosing what to let go of is a key growth area",
        1: "A quiet inner compass of quality — you know what's worth your energy",
        2: "Clear-eyed and discerning — you naturally distinguish what matters from what doesn't",
        3: "Sharp perception and strong principles — you bring structure and clarity wherever you go",
        4: "A natural architect of systems and boundaries — your precision and standards are exceptional",
    },
    "Water": {
        0: "Inner flow and intuition are an invitation — stillness may be your gateway to deeper wisdom",
        1: "A quiet well of intuition — you know things without knowing how you know them",
        2: "Deeply perceptive and adaptable — you read people and situations with ease",
        3: "Oceanic depth — your intuition, emotional intelligence, and wisdom run deep",
        4: "A vast inner world — your depth of perception and intuitive wisdom are profound",
    },
}

# Most/least abundant element insights
MOST_ABUNDANT_INSIGHTS = {
    "Wood": "You are someone who naturally generates ideas and sees the path forward — your vision is your gift.",
    "Fire": "You radiate warmth and passion naturally — people feel energized and seen in your presence.",
    "Earth": "You are the steady foundation — your groundedness and reliability are what others count on.",
    "Metal": "Your clarity, precision, and standards elevate everything you touch — you bring structure to chaos.",
    "Water": "Your depth, intuition, and emotional intelligence allow you to perceive what others overlook.",
}

LEAST_ABUNDANT_INSIGHTS = {
    "Wood": "This energy invites you to cultivate vision and new beginnings deliberately — growth doesn't have to be accidental.",
    "Fire": "This energy invites you to kindle self-expression consciously — your inner fire deserves to be seen.",
    "Earth": "This energy invites you to build grounded structures around your gifts so they endure beyond the spark.",
    "Metal": "This invites you to develop discernment — the art of choosing what truly matters and releasing what doesn't.",
    "Water": "This invites you to trust your intuition and inner flow — stillness may reveal depths busyness conceals.",
}


# ──────────────────────────────────────────────────────────────────────
# ANALYSIS: Five Element Balance
# ──────────────────────────────────────────────────────────────────────

# Map Chinese element names to English
_WUXING_CN_TO_EN = {"木": "Wood", "火": "Fire", "土": "Earth", "金": "Metal", "水": "Water"}

def compute_five_element_balance(chart: BaziChart) -> dict:
    """
    Count the five elements (Wood, Fire, Earth, Metal, Water)
    across all pillars: stems, branches, and hidden stems.
    Returns dict like {"Wood": 2, "Fire": 3, "Earth": 1, "Metal": 3, "Water": 2}.
    """
    balance = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}

    # Count main stems and branches for each pillar
    for pillar_key in ("year", "month", "day", "hour"):
        pillar = chart.to_dict()["pillars"][pillar_key]
        if not pillar:
            continue
        # Stem
        wx = _WUXING_CN_TO_EN.get(pillar["stem_wuxing"], "")
        if wx in balance:
            balance[wx] += 1
        # Branch
        wx = _WUXING_CN_TO_EN.get(pillar["branch_wuxing"], "")
        if wx in balance:
            balance[wx] += 1
        # Hidden stems (each counts as 1)
        for hs in pillar["hidden_stems"]:
            wx = _WUXING_CN_TO_EN.get(hs["wuxing"], "")
            if wx in balance:
                balance[wx] += 1

    return balance


# ──────────────────────────────────────────────────────────────────────
# ANALYSIS: Day Master Strength
# ──────────────────────────────────────────────────────────────────────

# Element generation cycle: generates (生)
_GENERATES = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
# Element conquest cycle: conquers (克)
_CONQUERS = {"Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"}

# Season mapping by month branch: season → set of month branches
_SEASON_BRANCHES = {
    "Spring": {3, 4, 5},     # 寅卯辰
    "Summer": {6, 7, 8},     # 巳午未
    "Autumn": {9, 10, 11},   # 申酉戌
    "Winter": {12, 1, 2},    # 亥子丑
}

# Which element rules which season
_SEASON_ELEMENT = {
    "Spring": "Wood",
    "Summer": "Fire",
    "Autumn": "Metal",
    "Winter": "Water",
    # Earth is inter-seasonal (last month of each season: 辰未戌丑)
}


def _get_season(month_branch: int) -> str:
    for season, branches in _SEASON_BRANCHES.items():
        if month_branch in branches:
            return season
    return "Autumn"  # fallback


def compute_day_master_strength(chart: BaziChart, balance: dict) -> str:
    """
    Heuristic day master strength assessment.
    
    A day master is:
    - "Strong" if it has >= 3 supporting elements and is in season
    - "Weak" if it has <= 1 supporting elements or is out of season with few supporters
    - "Balanced" otherwise
    
    Supporting elements: same element + the element that generates it.
    Opposing elements: the element it generates + the element that conquers it.
    """
    dm = chart.to_dict()["day_master"]
    dm_element_cn = dm["wuxing"]  # e.g. "金"
    dm_element = _WUXING_CN_TO_EN.get(dm_element_cn, dm_element_cn)  # → "Metal"

    # Supporting: same element + generating element
    supporting_count = balance.get(dm_element, 0)
    for src, tgt in _GENERATES.items():
        if tgt == dm_element:
            supporting_count += balance.get(src, 0)
            break

    # Opposing: generated element + conquering element
    opposing_count = balance.get(_GENERATES.get(dm_element, ""), 0)
    for conqueror, victim in _CONQUERS.items():
        if victim == dm_element:
            opposing_count += balance.get(conqueror, 0)
            break

    # Season check
    month_branch = chart.to_dict()["pillars"]["month"]["branch"]
    season = _get_season(month_branch)
    season_element = _SEASON_ELEMENT.get(season, "")

    in_season = (dm_element == season_element)
    # Earth is special: inter-seasonal (strong in 辰未戌丑 months)
    if dm_element == "Earth":
        earth_branches = {5, 8, 11, 2}  # 辰未戌丑
        in_season = month_branch in earth_branches

    score = supporting_count - opposing_count
    if in_season:
        score += 2

    if score >= 4:
        return "Strong"
    elif score <= 0:
        return "Weak"
    else:
        return "Balanced"


# ──────────────────────────────────────────────────────────────────────
# ANALYSIS: Useful / Annoying Gods
# ──────────────────────────────────────────────────────────────────────

def compute_useful_annoying_gods(dm_element: str, strength: str) -> tuple:
    """
    Determine Useful Gods (supportive elements) and Annoying Gods
    (growth-catalyst elements) based on day master strength.
    
    - Strong day master: useful = elements that conquer or drain it
    - Weak day master: useful = same element + element that generates it
    - Annoying = the remaining elements
    """
    generating = [e for e, g in _GENERATES.items() if g == dm_element]  # element that generates dm
    generated = [_GENERATES.get(dm_element, "")]  # element dm generates
    conquering = [e for e, v in _CONQUERS.items() if v == dm_element]  # element that conquers dm
    conquered = [_CONQUERS.get(dm_element, "")]  # element dm conquers

    all_elements = ["Wood", "Fire", "Earth", "Metal", "Water"]

    if strength == "Strong":
        # Drain or conquer the excess
        useful = [e for e in generated + conquering if e]
        annoying = [e for e in all_elements if e not in useful]
    elif strength == "Weak":
        # Support and nourish
        useful = [dm_element] + generating
        annoying = [e for e in all_elements if e not in useful]
    else:
        # Balanced: useful = elements that appear least in the chart
        # (simplified: just return the generating and same element as useful)
        useful = [dm_element] + generating
        annoying = [e for e in all_elements if e not in useful]

    return (useful, annoying)


# ──────────────────────────────────────────────────────────────────────
# PREVIEW GENERATION: Energy Theme
# ──────────────────────────────────────────────────────────────────────

ENERGY_THEMES = [
    {
        "condition": lambda s, ch: s.get("食神", 0) >= 1 or s.get("伤官", 0) >= 1,
        "gods": ["食神", "伤官"],
        "title": "From Creative Spark to Creative Legacy",
        "description": (
            "Your chart reveals an abundance of Creative Flow energy — you generate ideas, "
            "beauty, and inspiration almost effortlessly. The invitation woven into your "
            "blueprint is learning to pair that creative fire with discernment and structure. "
            "You're not here just to spark; you're here to build something that outlasts you."
        ),
        "question": "What might shift if you chose one creative project and gave it your undistracted attention for the next six months?",
    },
    {
        "condition": lambda s, ch: s.get("正官", 0) >= 1 or s.get("七杀", 0) >= 1,
        "gods": ["正官", "七杀"],
        "title": "Leading with Integrity — Your Natural Authority",
        "description": (
            "Your chart carries a strong compass of authority and discipline. You're someone "
            "others naturally respect and look to for direction. The invitation is to lead "
            "from your values, not from expectation — and to remember that the strongest "
            "leaders are those who know when to follow."
        ),
        "question": "Where in your life have you been following when your design calls you to lead?",
    },
    {
        "condition": lambda s, ch: s.get("正印", 0) >= 1 or s.get("偏印", 0) >= 1,
        "gods": ["正印", "偏印"],
        "title": "From Inner Knowing to Outer Expression",
        "description": (
            "You carry a rare depth of inner wisdom. Your chart shows strong Resource energy — "
            "you learn differently, through absorption and sudden clarity rather than brute-force "
            "study. The invitation is to trust that your voice matters enough to be heard. "
            "Your inner knowing deserves a bridge to the outer world."
        ),
        "question": "What insight have you been holding privately that the world might be ready to receive?",
    },
    {
        "condition": lambda s, ch: s.get("正财", 0) >= 1 or s.get("偏财", 0) >= 1,
        "gods": ["正财", "偏财"],
        "title": "The Art of Receiving — Allowing Abundance Without Chasing",
        "description": (
            "Your chart shows a strong relationship with resource and value. You have the "
            "capacity to build lasting material foundations. The invitation is learning that "
            "abundance flows more easily when you allow it rather than chase it — your natural "
            "stewardship of resources is the channel, not the chase."
        ),
        "question": "What might open up if you trusted that your value doesn't need to be proven — only expressed?",
    },
    {
        "condition": lambda s, ch: s.get("比肩", 0) >= 1 or s.get("劫财", 0) >= 1,
        "gods": ["比肩", "劫财"],
        "title": "Self-Reliance and the Power of Letting Others In",
        "description": (
            "Your chart carries strong self-reliance energy — you have a powerful sense of "
            "identity and a natural independence that others admire. The invitation woven "
            "into your blueprint is learning that true strength isn't about going it alone. "
            "Collaboration doesn't diminish your power — it multiplies it."
        ),
        "question": "What might become possible if you let one trusted person all the way in?",
    },
    {
        "condition": lambda s, ch: True,  # Default
        "gods": [],
        "title": "The Dance of Balance — Honoring All Parts of Your Design",
        "description": (
            "Your chart reveals a beautifully intricate design where multiple energies weave "
            "together. The invitation is to honor all parts of yourself — the bold and the "
            "quiet, the structured and the free. True mastery is not about amplifying one "
            "energy but learning the dance between them all."
        ),
        "question": "Which part of yourself have you been neglecting that is quietly asking for attention?",
    },
]


def pick_energy_theme(chart: BaziChart) -> dict:
    """Pick the most relevant energy theme based on Ten God frequency counts."""
    # Count Ten God appearances
    shishen_counts = {}
    for key, name in chart.shishen.items():
        if name != "日主":
            shishen_counts[name] = shishen_counts.get(name, 0) + 1

    # Score each theme by its specific Ten God counts
    best_theme = None
    best_score = -1
    for theme in ENERGY_THEMES:
        if not theme["condition"](shishen_counts, chart):
            continue
        # Compute score based on this theme's specific Ten God counts
        score = sum(shishen_counts.get(god, 0) for god in theme["gods"])
        if score > best_score:
            best_score = score
            best_theme = theme

    if best_theme is None:
        best_theme = ENERGY_THEMES[-1]

    return {
        "title": best_theme["title"],
        "description": best_theme["description"],
        "question": best_theme["question"],
    }


# ──────────────────────────────────────────────────────────────────────
# PREVIEW GENERATION: Fill template
# ──────────────────────────────────────────────────────────────────────

def generate_preview_text(
    chart: BaziChart,
    balance: dict,
    strength: str,
    name: str = "Friend",
    gender: str = "",
) -> str:
    """Generate the free preview email using the v2 template with variable substitution."""
    dm = chart.to_dict()["day_master"]
    dm_element = dm["wuxing"]
    dm_stem = dm["stem"]
    dm_polarity = "Yang" if dm["yinyang"] == "阳" else "Yin"

    archetype = DAY_MASTER_ARCHETYPES.get((dm_stem, dm["yinyang"]), f"the {dm_element} energy")
    personality = DAY_MASTER_PERSONALITY.get(dm_stem, "You carry a unique energetic signature.")

    # Most and least abundant elements
    sorted_el = sorted(balance.items(), key=lambda x: x[1], reverse=True)
    most_el, most_count = sorted_el[0]
    least_el, least_count = sorted_el[-1] if sorted_el[-1][1] < most_count else sorted_el[-2]

    # Energy theme
    theme = pick_energy_theme(chart)

    # Build element briefing lines
    element_lines = []
    for el in ["Wood", "Fire", "Earth", "Metal", "Water"]:
        count = balance.get(el, 0)
        icon = ELEMENT_ICONS.get(el, "")
        insight = ELEMENT_INSIGHTS.get(el, {}).get(min(count, 4), "")
        element_lines.append(f"{icon} {el} ({count}): {insight}")

    briefing = "\n".join(element_lines)

    preview = f"""Subject: {name}, your Energy Blueprint has been decoded ✨

---

Hi {name},

Your birth moment carries a unique energetic signature — and we've decoded it using BaZi, the 2,000-year-old Chinese system of elemental wisdom. Here is your first glimpse.

---

🌿 YOUR ELEMENTAL BRIEFING

Your chart's five-element balance reveals your natural energetic landscape:

{briefing}

Your most abundant energy is **{most_el}** — {MOST_ABUNDANT_INSIGHTS.get(most_el, '')} Your most catalytic energy — the one inviting your deepest growth — is **{least_el}**. {LEAST_ABUNDANT_INSIGHTS.get(least_el, '')}

---

🌀 YOUR CORE SELF

You are a **{dm_element} {dm_polarity}** Day Master — specifically the **{dm_stem}** energy, known as {archetype}.

{personality}

---

⚡ YOUR CURRENT ENERGY THEME

Based on the architecture of your chart, a theme that runs through your design is:

**{theme['title']}**

{theme['description']}

{theme['question']}

---

🔮 YOUR FULL BLUEPRINT AWAITS

This preview has shown you roughly 15% of what your Energy Blueprint contains. The **Complete Destiny Code Report** ($29) reveals the full picture — your full Personality Architecture, Relationship Mirror, Vocational Compass, all your Life Curricula, and practical integration guidance.

→ [Unlock Your Complete Report — $29]

---

With warmth,
The Destiny Code Team ⛩️

*Your Blueprint is a mirror, not a cage. Know your chart, then transcend it.*"""

    return preview


# ──────────────────────────────────────────────────────────────────────
# PREVIEW INSIGHTS: 2-3 short insight lines
# ──────────────────────────────────────────────────────────────────────

def generate_preview_insights(chart: BaziChart, balance: dict, strength: str) -> list:
    """Generate 2-3 short, punchy preview insights from chart data."""
    insights = []
    dm = chart.to_dict()["day_master"]

    # Insight 1: Day master identity
    dm_polarity_en = "Yang" if dm["yinyang"] == "阳" else "Yin"
    arch_long = DAY_MASTER_ARCHETYPES.get((dm["stem"], dm["yinyang"]), f"the {dm['wuxing']} energy")
    arch_short = arch_long.split(" — ")[0] if " — " in arch_long else arch_long
    insights.append(
        f"Your {dm_polarity_en} {dm['wuxing']} Day Master ({dm['stem']}) "
        f"gives you the archetype of {arch_short}"
    )

    # Insight 2: Most abundant element
    sorted_el = sorted(balance.items(), key=lambda x: x[1], reverse=True)
    most_el, most_count = sorted_el[0]
    insights.append(
        f"With {most_el} as your most abundant element ({most_count} appearances), "
        f"{most_el.lower()}-aligned gifts are your natural strength — "
        f"{'vision and growth' if most_el == 'Wood' else 'passion and expression' if most_el == 'Fire' else 'stability and grounding' if most_el == 'Earth' else 'clarity and discernment' if most_el == 'Metal' else 'wisdom and intuition'} flow through you effortlessly."
    )

    # Insight 3: Key Ten God
    ten_gods = {v: k for k, v in chart.shishen.items() if v != "日主" and k != "日"}
    if ten_gods:
        # Find most prominent non-日主 Ten God (simplified: pick one that's repeated)
        from collections import Counter
        god_counts = Counter(v for k, v in chart.shishen.items() if v != "日主")
        if god_counts:
            prominent_god = god_counts.most_common(1)[0][0]
            # Map to New Age name
            god_names = {
                "正官": "Inner Compass", "七杀": "Intensity Channel",
                "正印": "Wisdom Anchor", "偏印": "Unconventional Wisdom",
                "正财": "Steady Resources", "偏财": "Opportunity Magnet",
                "食神": "Creative Flow", "伤官": "Trailblazer Talent",
                "比肩": "Self-Reliance Core", "劫财": "Connection Catalyst",
            }
            na_name = god_names.get(prominent_god, prominent_god)
            insights.append(
                f"Your chart is anchored by {prominent_god} ({na_name}) energy — "
                f"showing up {god_counts[prominent_god]} times, this signature shapes how you engage the world."
            )

    return insights


# ──────────────────────────────────────────────────────────────────────
# HOOK LINE: one compelling sentence
# ──────────────────────────────────────────────────────────────────────

HOOK_TEMPLATES = {
    "Wood": "You are {polarity} Wood — the {archetype}. Your natural instinct is to grow, reach, and pioneer. But even the tallest tree needs deep roots.",
    "Fire": "You are {polarity} Fire — the {archetype}. Your warmth illuminates everything around you. The question is: where will you choose to shine?",
    "Earth": "You are {polarity} Earth — the {archetype}. You are the ground others build on. But mountains also deserve to be seen, not just leaned on.",
    "Metal": "You are {polarity} Metal — the {archetype}. Decisive, principled, and sharp. But even the finest sword must be tempered by wisdom.",
    "Water": "You are {polarity} Water — the {archetype}. Deep, intuitive, and fluid. Your depths hold wisdom most will never fathom — but are you ready to surface it?",
}


def generate_hook_line(chart: BaziChart) -> str:
    dm = chart.to_dict()["day_master"]
    polarity = "Yang" if dm["yinyang"] == "阳" else "Yin"
    element_cn = dm["wuxing"]
    element = _WUXING_CN_TO_EN.get(element_cn, element_cn)
    arch = DAY_MASTER_ARCHETYPES.get((dm["stem"], dm["yinyang"]), f"the {element} energy")
    short = arch.split(" — ")[0] if " — " in arch else arch
    # Remove leading "the " since HOOK_TEMPLATES already include "the"
    if short.startswith("the "):
        short = short[4:]
    archetype_short = short

    template = HOOK_TEMPLATES.get(element, "You are {polarity} {element} — your energy is unique and powerful.")
    return template.format(polarity=polarity, archetype=archetype_short, element=element)


# ──────────────────────────────────────────────────────────────────────
# MAIN: Pipeline orchestrator
# ──────────────────────────────────────────────────────────────────────

def run_pipeline(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    gender: str = "",
    name: str = "",
    json_output: bool = False,
) -> dict:
    """
    Run the full BaZi preview pipeline.

    Returns a dict with: chart data, analysis, preview text, insights, hook line.
    """
    # Step 1: Compute chart
    chart = compute_chart(year, month, day, hour, minute)
    chart_dict = chart.to_dict()

    # Step 2: Derive analysis data
    balance = compute_five_element_balance(chart)
    strength = compute_day_master_strength(chart, balance)
    useful, annoying = compute_useful_annoying_gods(
        _WUXING_CN_TO_EN.get(chart_dict["day_master"]["wuxing"], chart_dict["day_master"]["wuxing"]), strength
    )

    # Step 3: Generate preview components
    preview_text = generate_preview_text(chart, balance, strength, name=name or "Friend", gender=gender)
    insights = generate_preview_insights(chart, balance, strength)
    hook_line = generate_hook_line(chart)
    theme = pick_energy_theme(chart)

    # Step 4: Try AI analysis (uses MockAnalyzer in Phase 1)
    try:
        analyzer = MockAnalyzer()
        ai_analysis = analyze_chart(chart, "general", analyzer)
    except Exception:
        ai_analysis = "AI analysis unavailable."

    # Build output
    dm_en = _WUXING_CN_TO_EN.get(chart_dict["day_master"]["wuxing"], chart_dict["day_master"]["wuxing"])
    output = {
        "chart": chart_dict,
        "analysis": {
            "day_master": dm_en,
            "day_master_element": dm_en,
            "day_master_stem": chart_dict["day_master"]["stem"],
            "day_master_polarity": "Yang" if chart_dict["day_master"]["yinyang"] == "阳" else "Yin",
            "day_master_strength": strength,
            "day_master_archetype": DAY_MASTER_ARCHETYPES.get(
                (chart_dict["day_master"]["stem"], chart_dict["day_master"]["yinyang"]), ""
            ),
            "five_element_profile": balance,
            "useful_gods": useful,
            "annoying_gods": annoying,
            "energy_theme": theme["title"],
            "energy_theme_description": theme["description"],
            "curiosity_question": theme["question"],
        },
        "preview_insights": insights,
        "hook_line": hook_line,
        "preview_text": preview_text,
        "ai_raw": ai_analysis,
        "meta": {
            "pipeline_version": "1.0.0",
            "phase": "template-based",
            "input": {"year": year, "month": month, "day": day, "hour": hour, "minute": minute, "gender": gender},
        },
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="BaZi Preview Pipeline — 八字预览管道",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --year 1984 --month 6 --day 15 --hour 8 --json
  %(prog)s --year 2000 --month 1 --day 1 --hour 12 --gender F --name Maya --json""",
    )
    parser.add_argument("--year", type=int, required=True, help="Birth year (Gregorian)")
    parser.add_argument("--month", type=int, required=True, help="Birth month (1-12)")
    parser.add_argument("--day", type=int, required=True, help="Birth day (1-31)")
    parser.add_argument("--hour", type=int, default=0, help="Birth hour (0-23), default 0")
    parser.add_argument("--minute", type=int, default=0, help="Birth minute (0-59), default 0")
    parser.add_argument("--gender", type=str, default="", choices=["M", "F"], help="Gender (M/F)")
    parser.add_argument("--name", type=str, default="", help="Name for preview personalization")
    parser.add_argument("--json", action="store_true", help="Output structured JSON")

    args = parser.parse_args()

    result = run_pipeline(
        year=args.year,
        month=args.month,
        day=args.day,
        hour=args.hour,
        minute=args.minute,
        gender=args.gender,
        name=args.name,
        json_output=args.json,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Text output: chart display + preview
        chart = compute_chart(args.year, args.month, args.day, args.hour, args.minute)
        print(chart.display())
        print()
        print("─" * 50)
        print("  PREVIEW TEXT")
        print("─" * 50)
        print(result["preview_text"])


if __name__ == "__main__":
    main()
