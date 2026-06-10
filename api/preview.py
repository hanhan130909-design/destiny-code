"""
Destiny Code — Enhanced Preview API (V2)
Vercel Serverless Function

Computes full BaZi chart using core.py, applies True Solar Time correction,
and optionally generates AI interpretation via DeepSeek.

POST /api/preview
{
  "name": "string",
  "birthdate": "YYYY-MM-DD",
  "birthtime": "HH:MM",
  "birthplace": "City, Country",
  "email": "optional"
}
"""
import sys
import os
import json
import traceback

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
import requests

# ── Imports from our BaZi core ────────────────────────────────────────
try:
    from api.core import compute_chart
    from api.constants import (
        TIANGAN, TIANGAN_PINYIN, TIANGAN_WUXING, TIANGAN_YINYANG,
        DIZHI, DIZHI_PINYIN, DIZHI_WUXING, DIZHI_YINYANG,
    )
    HAS_CORE = True
except ImportError:
    HAS_CORE = False

# ── Env ────────────────────────────────────────────────────────────────
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "Destiny Code <onboarding@resend.dev>")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# ── Solar Term reference for month pillar ─────────────────────────────
# Simple LiChun dates: year → (month, day)
_LICHUN = {
    2024: (2,4), 2025: (2,3), 2026: (2,4), 2027: (2,4), 2028: (2,4),
    2029: (2,3), 2030: (2,4),
}

# Standalone pillar computation (used when core.py unavailable)
import datetime as _dt
_REF_DATE = _dt.date(1900, 1, 1)
_REF_STEM = 1
_REF_BRANCH = 11

def _day_pillar_simple(y, m, d):
    delta = (_dt.date(y, m, d) - _REF_DATE).days
    stem = ((_REF_STEM - 1 + delta) % 10) + 1
    branch = ((_REF_BRANCH - 1 + delta) % 12) + 1
    return stem, branch

def _year_pillar_simple(year, month, day):
    lc = _LICHUN.get(year, (2, 4))
    if month < lc[0] or (month == lc[0] and day < lc[1]):
        year -= 1
    stem = ((year - 4) % 10) + 1
    branch = ((year - 4) % 12) + 1
    return stem, branch

_MONTH_STEM_TABLE = {
    1: {1:3,2:4,3:5,4:6,5:7,6:8,7:9,8:10,9:1,10:2,11:3,12:4},
    2: {1:5,2:6,3:7,4:8,5:9,6:10,7:1,8:2,9:3,10:4,11:5,12:6},
    3: {1:7,2:8,3:9,4:10,5:1,6:2,7:3,8:4,9:5,10:6,11:7,12:8},
    4: {1:9,2:10,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10},
    5: {1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:1,12:2},
}
_STEM_GROUPS = {1:1, 6:1, 2:2, 7:2, 3:3, 8:3, 4:4, 9:4, 5:5, 10:5}
_MONTH_BRANCH = {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,12:1}
_HOUR_BRANCH = {23:1,0:1,1:2,3:3,5:4,7:5,9:6,11:7,13:8,15:9,17:10,19:11,21:12}
_HOUR_STEM_TABLE = {
    1: {1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:1,12:2},
    2: {1:3,2:4,3:5,4:6,5:7,6:8,7:9,8:10,9:1,10:2,11:3,12:4},
    3: {1:5,2:6,3:7,4:8,5:9,6:10,7:1,8:2,9:3,10:4,11:5,12:6},
    4: {1:7,2:8,3:9,4:10,5:1,6:2,7:3,8:4,9:5,10:6,11:7,12:8},
    5: {1:9,2:10,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10},
}

# ── Day Master Archetypes ──────────────────────────────────────────────
_ARCHETYPES = {
    ("Jia","Yang"): "the towering tree — pioneer spirit and natural leadership",
    ("Yi","Yin"): "the resilient vine — graceful, adaptable, and quietly unstoppable",
    ("Bing","Yang"): "the sun itself — radiant, generous, and impossible to ignore",
    ("Ding","Yin"): "the candle flame — warm, magnetic, with a light that draws others close",
    ("Wu","Yang"): "the mountain — steady, protective, and immovable when it matters",
    ("Ji","Yin"): "the fertile soil — nurturing, resourceful, the ground where things grow",
    ("Geng","Yang"): "the sword — decisive, principled, with a natural instinct for justice",
    ("Xin","Yin"): "the jewel — refined, discerning, with an eye for what truly matters",
    ("Ren","Yang"): "the ocean — visionary, expansive, carrying depths most never see",
    ("Gui","Yin"): "the mist — subtle, intuitive, a quiet wisdom that permeates everything",
}

_ENERGY_THEMES = {
    "Wood":"Growth & Vision","Fire":"Passion & Expression","Earth":"Stability & Nurturing",
    "Metal":"Clarity & Precision","Water":"Wisdom & Intuition",
}

_GROWTH_EDGES = {
    "Jia": "Your forward momentum can overwhelm others — true strength sometimes means pausing so they can catch up.",
    "Yi": "Grace becomes avoidance when overused — sometimes the most elegant path is the direct one.",
    "Bing": "The sun doesn't need to shine at full intensity in every moment to be powerful. Learn to sustain your fire without burning out.",
    "Ding": "Trust that your gentle light is enough — you don't need to burn brighter to matter.",
    "Wu": "The mountain that never shifts becomes isolated from the changing landscape. Learn to bend.",
    "Ji": "Remember to nurture yourself with the same generosity you extend to everyone else.",
    "Geng": "The sword that's too sharp breaks. Truth delivered without care becomes cruelty — soften your delivery.",
    "Xin": "Your eye for quality can become a barrier to connection. Perfection is a direction, not a destination.",
    "Ren": "The ocean's depth can become isolation. Let people sail your waters — they can't navigate what they can't see.",
    "Gui": "Your quiet wisdom needs to find its voice. The mist that never lifts leaves others lost.",
}

# ── True Solar Time correction ─────────────────────────────────────────
_CITY_LONGITUDE = {
    "beijing": 116.4, "shanghai": 121.5, "tokyo": 139.8, "seoul": 127.0,
    "hong kong": 114.2, "singapore": 103.8, "taipei": 121.5, "shenzhen": 114.1,
    "guangzhou": 113.3, "delhi": 77.2, "mumbai": 72.8, "kolkata": 88.4,
    "bangkok": 100.5, "ho chi minh": 106.6, "hanoi": 105.8,
    "london": -0.1, "paris": 2.3, "berlin": 13.4, "rome": 12.5, "madrid": -3.7,
    "new york": -74.0, "los angeles": -118.2, "chicago": -87.6, "houston": -95.4,
    "san francisco": -122.4, "toronto": -79.4, "vancouver": -123.1,
    "sydney": 151.2, "melbourne": 145.0, "auckland": 174.8, "perth": 115.9,
    "moscow": 37.6, "istanbul": 29.0, "dubai": 55.3, "cairo": 31.2,
    "sao paulo": -46.6, "buenos aires": -58.4, "mexico city": -99.1,
    "kuala lumpur": 101.7, "jakarta": 106.8, "manila": 121.0,
}

def _get_longitude(birthplace: str) -> float:
    """Extract longitude from birthplace string. Returns 0 if unknown."""
    if not birthplace:
        return 0.0
    city_lower = birthplace.lower().split(",")[0].strip()
    # Exact match
    if city_lower in _CITY_LONGITUDE:
        return _CITY_LONGITUDE[city_lower]
    # Partial match
    for known_city, lon in _CITY_LONGITUDE.items():
        if known_city in city_lower or city_lower in known_city:
            return lon
    return 0.0

def apply_true_solar_time(hour: int, minute: int, birthplace: str) -> tuple:
    """Apply True Solar Time correction based on longitude.
    Returns (corrected_hour, corrected_minute).
    """
    lon = _get_longitude(birthplace)
    if lon == 0.0:
        return hour, minute
    # Standard time zone meridian (rough; China=120°E, most countries use nearest 15°)
    if 75 <= lon <= 135:
        std_meridian = 120  # UTC+8
    elif lon < 75:
        std_meridian = round(lon / 15) * 15
    else:
        std_meridian = round(lon / 15) * 15
    # Time correction: 4 minutes per degree of longitude difference
    delta_min = (lon - std_meridian) * 4
    total_min = hour * 60 + minute + delta_min
    total_min = total_min % (24 * 60)
    if total_min < 0:
        total_min += 24 * 60
    return int(total_min // 60), int(total_min % 60)

# ── Chart Computation ──────────────────────────────────────────────────

def compute_bazi_chart(year, month, day, hour=12, minute=0, birthplace=""):
    """Compute full BaZi chart. Uses core.py if available, falls back to simple calc."""
    
    # Apply True Solar Time
    if birthplace:
        corrected_hour, corrected_minute = apply_true_solar_time(hour, minute, birthplace)
    else:
        corrected_hour, corrected_minute = hour, minute
    
    use_core = HAS_CORE

    if use_core:
        try:
            chart = compute_chart(year, month, day, corrected_hour, corrected_minute)
            chart_dict = chart.to_dict()

            # Build the result
            dm = chart_dict["day_master"]
            dm_name = dm["stem"]
            dm_wx = dm["wuxing"]
            dm_yy = dm["yinyang"]

            # Map to English/Pinyin
            wx_en = {"木": "Wood", "火": "Fire", "土": "Earth", "金": "Metal", "水": "Water"}
            yy_en = {"阳": "Yang", "阴": "Yin"}
            pinyin_map = {"甲":"Jia","乙":"Yi","丙":"Bing","丁":"Ding","戊":"Wu","己":"Ji","庚":"Geng","辛":"Xin","壬":"Ren","癸":"Gui"}

            dm_name_en = pinyin_map.get(dm_name, dm_name)
            dm_wx_en = wx_en.get(dm_wx, dm_wx)
            dm_yy_en = yy_en.get(dm_yy, dm_yy)

            pillars = chart_dict["pillars"]
            year_pillar = pillars["year"]
            month_pillar = pillars["month"]
            day_pillar = pillars["day"]
            hour_pillar = pillars["hour"]

            # Count five elements across all 8 characters
            elements = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
            for p in [year_pillar, month_pillar, day_pillar, hour_pillar]:
                swx = p.get("stem_wuxing", "")
                bwx = p.get("branch_wuxing", "")
                if swx in wx_en:
                    elements[wx_en[swx]] += 1
                if bwx in wx_en:
                    elements[wx_en[bwx]] += 1

            # Dominant and weakest
            sorted_el = sorted(elements.items(), key=lambda x: -x[1])
            dominant = sorted_el[0][0]
            weakest = sorted_el[-1][0]
            max_count = sorted_el[0][1]
            min_count = sorted_el[-1][1]
            
            if max_count >= 4:
                balance = "strongly dominated"
                balance_detail = f"Your chart is strongly dominated by {dominant} energy. This gives you clear strengths but can create blind spots in other areas."
            elif max_count >= 3 and min_count <= 1:
                balance = "imbalanced"
                balance_detail = f"Your chart shows an imbalance — strong {dominant} with very little {weakest}. Balancing these energies is a key growth theme."
            elif max_count <= 2:
                balance = "well-distributed"
                balance_detail = "Your elemental energies are well-distributed. This gives you versatility and adaptability across different life domains."
            else:
                balance = "moderately balanced"
                balance_detail = f"Your chart leans toward {dominant} energy while maintaining reasonable access to all elements."

            archetype = _ARCHETYPES.get((dm_name_en, dm_yy_en), "a unique and powerful configuration")
            energy_theme = _ENERGY_THEMES.get(dm_wx_en, "Self-Discovery")
            growth_edge = _GROWTH_EDGES.get(dm_name_en, "Understanding your energy patterns is the first step toward growth.")

            # Build Ten Gods from the chart data
            shishen = chart_dict.get("shishen", {})
            ten_gods = {
                "year": shishen.get("年", ""),
                "month": shishen.get("月", ""),
                "day": shishen.get("日", ""),
                "hour": shishen.get("时", ""),
            }

            # Build hidden stems
            hidden_stems = day_pillar.get("hidden_stems", [])

            return {
                "day_master": dm_name_en,
                "day_master_wuxing": dm_wx_en,
                "day_master_yinyang": dm_yy_en,
                "archetype": archetype,
                "energy_theme": energy_theme,
                "elements": elements,
                "dominant": dominant,
                "weakest": weakest,
                "balance": balance,
                "balance_detail": balance_detail,
                "growth_edge": growth_edge,
                "pillars": {
                    "year": f"{year_pillar.get('stem_pinyin', year_pillar['stem_name'])}{year_pillar.get('branch_pinyin', year_pillar['branch_name'])}",
                    "month": f"{month_pillar.get('stem_pinyin', month_pillar['stem_name'])}{month_pillar.get('branch_pinyin', month_pillar['branch_name'])}",
                    "day": f"{day_pillar.get('stem_pinyin', day_pillar['stem_name'])}{day_pillar.get('branch_pinyin', day_pillar['branch_name'])}",
                    "hour": f"{hour_pillar.get('stem_pinyin', hour_pillar['stem_name'])}{hour_pillar.get('branch_pinyin', hour_pillar['branch_name'])}",
                },
                "pillars_detailed": {
                    "year": year_pillar,
                    "month": month_pillar,
                    "day": day_pillar,
                    "hour": hour_pillar,
                },
                "ten_gods": ten_gods,
                "hidden_stems": hidden_stems,
                "xunkong": chart_dict.get("xunkong", []),
                "solar_time": bool(birthplace),
                "solar_time_hour": corrected_hour,
                "solar_time_minute": corrected_minute,
            }
        except Exception as e:
            use_core = False
            # Fall back to simple calculation below

    # ── Simple standalone calculation ───────────────────────────────
    ys, yb = _year_pillar_simple(year, month, day)
    ms, mb = _month_pillar_simple(ys, month)
    ds, db = _day_pillar_simple(year, month, day)
    hs, hb = _hour_pillar_simple(ds, corrected_hour)

    # Use Pinyin names
    _TG_EN = ["", "Jia","Yi","Bing","Ding","Wu","Ji","Geng","Xin","Ren","Gui"]
    _TG_WX = ["", "Wood","Wood","Fire","Fire","Earth","Earth","Metal","Metal","Water","Water"]
    _TG_YY = ["", "Yang","Yin","Yang","Yin","Yang","Yin","Yang","Yin","Yang","Yin"]
    _DZ_EN = ["", "Zi","Chou","Yin","Mao","Chen","Si","Wu","Wei","Shen","You","Xu","Hai"]
    _DZ_WX = ["", "Water","Earth","Wood","Wood","Earth","Fire","Fire","Earth","Metal","Metal","Earth","Water"]

    dm_name = _TG_EN[ds]
    dm_wx = _TG_WX[ds]
    dm_yy = _TG_YY[ds]

    elements = {"Wood":0,"Fire":0,"Earth":0,"Metal":0,"Water":0}
    for s in [ys,ms,ds,hs]: elements[_TG_WX[s]] += 1
    for b in [yb,mb,db,hb]: elements[_DZ_WX[b]] += 1

    sorted_el = sorted(elements.items(), key=lambda x: -x[1])
    dominant = sorted_el[0][0]
    weakest = sorted_el[-1][0]
    max_count = sorted_el[0][1]
    min_count = sorted_el[-1][1]

    if max_count >= 4:
        balance = "strongly dominated"
        balance_detail = f"Your chart is strongly dominated by {dominant} energy. This gives you clear strengths but can create blind spots in other areas."
    elif max_count >= 3 and min_count <= 1:
        balance = "imbalanced"
        balance_detail = f"Your chart shows an imbalance — strong {dominant} with very little {weakest}. Balancing these energies is a key growth theme."
    elif max_count <= 2:
        balance = "well-distributed"
        balance_detail = "Your elemental energies are well-distributed. This gives you versatility and adaptability across different life domains."
    else:
        balance = "moderately balanced"
        balance_detail = f"Your chart leans toward {dominant} energy while maintaining reasonable access to all elements."

    archetype = _ARCHETYPES.get((dm_name, dm_yy), "a unique and powerful configuration")
    energy_theme = _ENERGY_THEMES.get(dm_wx, "Self-Discovery")
    growth_edge = _GROWTH_EDGES.get(dm_name, "Understanding your energy patterns is the first step toward growth.")

    return {
        "day_master": dm_name,
        "day_master_wuxing": dm_wx,
        "day_master_yinyang": dm_yy,
        "archetype": archetype,
        "energy_theme": energy_theme,
        "elements": elements,
        "dominant": dominant,
        "weakest": weakest,
        "balance": balance,
        "balance_detail": balance_detail,
        "growth_edge": growth_edge,
        "pillars": {
            "year": f"{_TG_EN[ys]}{_DZ_EN[yb]}",
            "month": f"{_TG_EN[ms]}{_DZ_EN[mb]}",
            "day": f"{_TG_EN[ds]}{_DZ_EN[db]}",
            "hour": f"{_TG_EN[hs]}{_DZ_EN[hb]}",
        },
        "ten_gods": {},
        "hidden_stems": [],
        "xunkong": [],
        "solar_time": bool(birthplace),
        "solar_time_hour": corrected_hour,
        "solar_time_minute": corrected_minute,
    }

# Standalone helpers (used when core.py unavailable)
def _month_pillar_simple(ys, month):
    group = _STEM_GROUPS.get(ys, 1)
    stem = _MONTH_STEM_TABLE[group][month]
    branch = _MONTH_BRANCH[month]
    return stem, branch

def _hour_pillar_simple(ds, hour):
    branch = _HOUR_BRANCH.get(hour, 1)
    group = _STEM_GROUPS.get(ds, 1)
    stem = _HOUR_STEM_TABLE[group][branch]
    return stem, branch

# ── AI Interpretation ──────────────────────────────────────────────────

def generate_ai_interpretation(chart_data: dict, name: str) -> str:
    """Generate AI interpretation using DeepSeek API."""
    if not DEEPSEEK_API_KEY:
        return ""

    # Build the chart JSON in the format the system prompt expects
    pillars = chart_data.get("pillars", {})
    elements = chart_data.get("elements", {})

    chart_json = {
        "name": name,
        "birthDate": "",
        "birthTime": "",
        "birthPlace": "",
        "gender": "N",
        "chart": {
            "yearPillar": {"stem": pillars.get("year", ""), "branch": pillars.get("year", ""), "hiddenStems": []},
            "monthPillar": {"stem": pillars.get("month", ""), "branch": pillars.get("month", ""), "hiddenStems": []},
            "dayPillar": {"stem": pillars.get("day", ""), "branch": pillars.get("day", ""), "hiddenStems": []},
            "hourPillar": {"stem": pillars.get("hour", ""), "branch": pillars.get("hour", ""), "hiddenStems": []},
        },
        "dayMaster": {
            "stem": f"{chart_data['day_master']}({chart_data['day_master']})",
            "element": chart_data["day_master_wuxing"],
            "polarity": chart_data["day_master_yinyang"],
        },
        "tenGods": chart_data.get("ten_gods", {}),
        "fiveElementsBalance": elements,
        "dayMasterStrength": "Balanced",  # simplified
        "usefulGods": [chart_data["dominant"]],
        "annoyingGods": [chart_data["weakest"]],
    }

    # The full system prompt from bazi-system-prompt-v2.md (abbreviated for API)
    system_prompt = """You are the Destiny Code Interpreter — a warm, precise, and empowering BaZi (Eight Characters / Four Pillars of Destiny) reader. You translate ancient Chinese elemental wisdom into a modern "Personal Energy Blueprint" for a Western, spiritually-curious audience. You are a mirror, not a fortune-teller.

CRITICAL CONSTRAINTS:
1. No fear language: never say "bad luck", "disaster", "misfortune", "curse", "danger", "warning", "threat".
2. No specific predictions: never predict death, accidents, illness, financial ruin, or exact dates.
3. Reframe all challenges positively: "growth edge" not "weakness", "life curriculum" not "problem".
4. No religious language: no God, Buddha, sin, karma. Use: universe, cosmic rhythm, life force, natural flow.
5. Affirm agency: BaZi reveals tendencies only — the individual always has choice.

OUTPUT: Generate a warm, personal report in 7 sections (500-800 words total):
1. Cosmic Signature (~80 words): Greeting with name, Day Master element + archetype.
2. Elemental Landscape (~100 words): Walk through five elements distribution.
3. Personality Architecture (~200 words): Day Master personality + key Ten Gods traits.
4. Life's Curriculum (~100 words): 1-2 key life themes as "soul invitations".
5. Mirror of Relationships (~100 words): Natural relational style.
6. Vocational Compass (~100 words): 2-3 career directions aligned with elements.
7. Integration (~80 words): Warm summary + one practical experiment for the week.

End with: "Your Energy Blueprint is a mirror — it reflects your innate patterns so you can partner with them consciously. The ancient sages said: know your chart, then transcend it."

Use these Day Master archetypes:
Jia Wood Yang — the towering tree, pioneer. Yi Wood Yin — the resilient vine. Bing Fire Yang — the sun. Ding Fire Yin — the candle flame. Wu Earth Yang — the mountain. Ji Earth Yin — the fertile soil. Geng Metal Yang — the sword. Xin Metal Yin — the jewel. Ren Water Yang — the ocean. Gui Water Yin — the mist."""

    user_prompt = f"""Interpret this BaZi chart for {name}:

```json
{json.dumps(chart_json, indent=2, ensure_ascii=False)}
```

Generate a complete Energy Blueprint report following the 7-section structure. Make it personal, warm, and address {name} directly."""

    try:
        resp = requests.post(
            f"{DEEPSEEK_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        else:
            print(f"DeepSeek API error: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"DeepSeek API exception: {e}", file=sys.stderr)
        return ""

# ── Email ──────────────────────────────────────────────────────────────

def send_preview_email(to_email, to_name, chart_data):
    if not RESEND_API_KEY:
        return {"sent": False, "error": "No RESEND_API_KEY"}
    dm = chart_data["day_master"]
    wx = chart_data["day_master_wuxing"]
    html = f"""<!DOCTYPE html>
<html><body style="font-family:Georgia,serif;background:#0a0c14;color:#c8ccd6;padding:40px 20px">
<div style="max-width:560px;margin:0 auto;background:#111520;border:1px solid #1e2433;border-radius:12px;padding:32px">
<div style="text-align:center;margin-bottom:24px">
  <div style="font-size:32px">☯</div>
  <h1 style="color:#e8ecf1;font-size:22px">Your Energy Blueprint Preview</h1>
  <p style="color:#6b7280;font-size:13px">Prepared for <strong style="color:#c9a96e">{to_name}</strong></p>
</div>
<div style="background:#0a0c14;border:1px solid #1e2433;border-radius:8px;padding:20px;margin:20px 0;text-align:center">
  <p style="color:#c9a96e;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px">Your Day Master</p>
  <h2 style="color:#e8ecf1;font-size:30px;margin:0 0 8px">{dm} <span style="color:#c9a96e;font-size:18px">({wx})</span></h2>
  <p style="color:#8b7348;font-size:14px;margin:0">{chart_data['archetype']}</p>
</div>
<div style="text-align:center;margin:28px 0">
  <a href="https://metaphysics-landing.vercel.app/free-bazi-calculator" style="display:inline-block;background:#c9a96e;color:#0a0c14;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px">See Your Full Blueprint →</a>
</div>
<div style="border-top:1px solid #1e2433;padding-top:16px;margin-top:24px">
  <p style="font-size:11px;color:#5c5770;text-align:center">Destiny Code — Your Personal Energy Blueprint<br>This is a one-time preview. No spam, no subscription.</p>
</div>
</div></body></html>"""

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": FROM_EMAIL, "to": to_email, "subject": f"{to_name}, your Destiny Code preview is ready ✦", "html": html},
            timeout=10,
        )
        if resp.status_code == 200:
            return {"sent": True, "id": resp.json().get("id", "")}
        return {"sent": False, "error": resp.text[:200]}
    except Exception as e:
        return {"sent": False, "error": str(e)}


# ── HTTP Handler ───────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        name = (data.get("name") or "").strip()
        birthdate = (data.get("birthdate") or "").strip()
        birthtime = (data.get("birthtime") or "12:00").strip()
        birthplace = (data.get("birthplace") or "").strip()
        email = (data.get("email") or "").strip()

        if not name or not birthdate:
            self._respond(400, {"error": "Missing name or birthdate"})
            return

        # Parse date
        try:
            parts = birthdate.split("-")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            self._respond(400, {"error": "Invalid birthdate. Use YYYY-MM-DD."})
            return

        # Parse time
        hour, minute = 12, 0
        if birthtime:
            try:
                tp = birthtime.split(":")
                hour, minute = int(tp[0]), int(tp[1]) if len(tp) > 1 else 0
            except (ValueError, IndexError):
                pass

        # Compute chart
        try:
            chart_data = compute_bazi_chart(year, month, day, hour, minute, birthplace)
        except Exception as e:
            traceback.print_exc()
            self._respond(500, {"error": f"Chart computation failed: {str(e)}"})
            return

        # Email (non-blocking — best effort)
        email_result = {"sent": False}
        if email:
            email_result = send_preview_email(email, name, chart_data)

        # AI interpretation (synchronous — user waits but gets full report)
        ai_text = ""
        if DEEPSEEK_API_KEY:
            try:
                ai_text = generate_ai_interpretation(chart_data, name)
            except Exception as e:
                ai_text = ""

        response = {
            "ok": True,
            **chart_data,
            "ai_interpretation": ai_text,
            "email_sent": email_result.get("sent", False),
        }
        self._respond(200, response)

    def do_GET(self):
        self._respond(200, {"status": "ok", "service": "Destiny Code Preview API V2"})

    def _respond(self, status_code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
