"""
Vercel Serverless Function — Destiny Code Preview API

Receives Formspree webhook → computes BaZi chart → generates preview → sends email via Resend.

Deploy: place bazi_chart/ module in project root alongside this file.
"""

import sys
import os
import json
import requests
from http.server import BaseHTTPRequestHandler

# Resend API key — set in Vercel environment variables
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "Destiny Code <onboarding@resend.dev>")

# ── Day Master Archetypes ──────────────────────────────────────────────

DAY_MASTER_ARCHETYPES = {
    ("Jia", "Yang"): "the towering tree — pioneer spirit and natural leadership",
    ("Yi", "Yin"): "the resilient vine — graceful, adaptable, and quietly unstoppable",
    ("Bing", "Yang"): "the sun itself — radiant, generous, and impossible to ignore",
    ("Ding", "Yin"): "the candle flame — warm, magnetic, with a light that draws others close",
    ("Wu", "Yang"): "the mountain — steady, protective, and immovable when it matters",
    ("Ji", "Yin"): "the fertile soil — nurturing, resourceful, the ground where things grow",
    ("Geng", "Yang"): "the sword — decisive, principled, with a natural instinct for justice",
    ("Xin", "Yin"): "the jewel — refined, discerning, with an eye for what truly matters",
    ("Ren", "Yang"): "the ocean — visionary, expansive, carrying depths most never see",
    ("Gui", "Yin"): "the mist — subtle, intuitive, a quiet wisdom that permeates everything",
}

ENERGY_THEMES = {
    "Wood": "Growth & Vision",
    "Fire": "Passion & Expression",
    "Earth": "Stability & Nurturing",
    "Metal": "Clarity & Precision",
    "Water": "Wisdom & Intuition",
}

GROWTH_EDGES = {
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

# ── Wuxing (Five Elements) ─────────────────────────────────────────────

TIANGAN = ["", "Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
TIANGAN_WUXING = ["", "Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]
TIANGAN_YINYANG = ["", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"]
DIZHI = ["", "Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
DIZHI_WUXING = ["", "Water", "Earth", "Wood", "Wood", "Earth", "Fire", "Fire", "Earth", "Metal", "Metal", "Earth", "Water"]
DIZHI_YINYANG = ["", "Yang", "Yin", "Yang", "Yin", "Yang", "Yang", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"]

# ── BaZi Calculation Core ──────────────────────────────────────────────

import datetime

_REF_DATE = datetime.date(1900, 1, 1)
_REF_STEM = 1
_REF_BRANCH = 11

def day_pillar(year, month, day):
    """Compute day stem and branch (1-indexed)."""
    d = datetime.date(year, month, day)
    delta = (d - _REF_DATE).days
    stem = ((_REF_STEM - 1 + delta) % 10) + 1
    branch = ((_REF_BRANCH - 1 + delta) % 12) + 1
    return stem, branch

def year_pillar(year, month, day):
    """Compute year pillar — sexagenary year begins at Li Chun (~Feb 4)."""
    # Simple Li Chun check: before Feb 4 → use previous year
    if month < 2 or (month == 2 and day < 4):
        year -= 1
    stem = ((year - 4) % 10) + 1
    branch = ((year - 4) % 12) + 1
    return stem, branch

# Month stem lookup: (year_stem_group, month_num) → stem
# Groups: Jia/Ji=1, Yi/Geng=2, Bing/Xin=3, Ding/Ren=4, Wu/Gui=5
_MONTH_STEM = {
    1: {1:3,2:4,3:5,4:6,5:7,6:8,7:9,8:10,9:1,10:2,11:3,12:4},
    2: {1:5,2:6,3:7,4:8,5:9,6:10,7:1,8:2,9:3,10:4,11:5,12:6},
    3: {1:7,2:8,3:9,4:10,5:1,6:2,7:3,8:4,9:5,10:6,11:7,12:8},
    4: {1:9,2:10,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10},
    5: {1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:1,12:2},
}

_STEM_GROUPS = {1:1, 6:1, 2:2, 7:2, 3:3, 8:3, 4:4, 9:4, 5:5, 10:5}

# Month branches: Zi=11(Dec), Chou=12(Jan), Yin=1(Feb), Mao=2(Mar)...
# Solar month starts around 4th-8th of each Gregorian month
# Simplified: month_num → earthly branch
_MONTH_BRANCH = {1:2, 2:3, 3:4, 4:5, 5:6, 6:7, 7:8, 8:9, 9:10, 10:11, 11:12, 12:1}

def month_pillar(year_stem, month):
    """Compute month pillar."""
    group = _STEM_GROUPS.get(year_stem, 1)
    stem = _MONTH_STEM[group][month]
    branch = _MONTH_BRANCH[month]
    return stem, branch

# Hour branches (Shi Chen)
_HOUR_BRANCH = {23:1,0:1, 1:2, 3:3, 5:4, 7:5, 9:6, 11:7, 13:8, 15:9, 17:10, 19:11, 21:12}

# Hour stem: (day_stem_group, hour_branch) → stem
_HOUR_STEM = {
    1: {1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:1,12:2},
    2: {1:3,2:4,3:5,4:6,5:7,6:8,7:9,8:10,9:1,10:2,11:3,12:4},
    3: {1:5,2:6,3:7,4:8,5:9,6:10,7:1,8:2,9:3,10:4,11:5,12:6},
    4: {1:7,2:8,3:9,4:10,5:1,6:2,7:3,8:4,9:5,10:6,11:7,12:8},
    5: {1:9,2:10,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10},
}

def hour_pillar(day_stem, hour):
    """Compute hour pillar."""
    branch = _HOUR_BRANCH.get(hour, 1)
    group = _STEM_GROUPS.get(day_stem, 1)
    stem = _HOUR_STEM[group][branch]
    return stem, branch

def compute_chart(year, month, day, hour=0):
    """Compute full BaZi chart and return analysis dict."""
    ys, yb = year_pillar(year, month, day)
    ms, mb = month_pillar(ys, month)
    ds, db = day_pillar(year, month, day)
    hs, hb = hour_pillar(ds, hour)

    day_stem_name = TIANGAN[ds]
    day_wuxing = TIANGAN_WUXING[ds]
    day_yinyang = TIANGAN_YINYANG[ds]

    # Count five elements across all stems and branches
    elements = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    for stem_idx in [ys, ms, ds, hs]:
        elements[TIANGAN_WUXING[stem_idx]] += 1
    for branch_idx in [yb, mb, db, hb]:
        elements[DIZHI_WUXING[branch_idx]] += 1

    # Find dominant and weakest elements
    sorted_el = sorted(elements.items(), key=lambda x: -x[1])
    dominant = sorted_el[0][0]
    weakest = sorted_el[-1][0]

    # Element balance assessment
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

    # Archetype
    archetype = DAY_MASTER_ARCHETYPES.get((day_stem_name, day_yinyang), "a unique and powerful configuration")

    # Energy theme
    energy_theme = ENERGY_THEMES.get(day_wuxing, "Self-Discovery")

    # Growth edge
    growth_edge = GROWTH_EDGES.get(day_stem_name, "Understanding your energy patterns is the first step toward growth.")

    # Generate preview text
    preview_text = f"""Your Day Master is the {day_stem_name} ({day_yinyang} {day_wuxing}) — {archetype}.

As a {day_wuxing} type, your core energy theme is: {energy_theme}. {balance_detail}

In relationships and daily interactions, you naturally express as {TIANGAN_WUXING[ds]} energy — {'direct and outward-facing' if day_yinyang == 'Yang' else 'receptive and inwardly powerful'}. Your elemental profile shows dominant {dominant} ({max_count} appearances) and relatively less {weakest} ({min_count} appearances).

Key Growth Edge: {growth_edge}

This is just a snapshot. Your full Energy Blueprint maps all Four Pillars — Year, Month, Day, and Hour — revealing your complete personality matrix, relationship dynamics, career path, and life chapter timing."""

    return {
        "day_master": day_stem_name,
        "day_master_pinyin": day_stem_name,
        "day_master_wuxing": day_wuxing,
        "day_master_yinyang": day_yinyang,
        "archetype": archetype,
        "energy_theme": energy_theme,
        "elements": elements,
        "dominant": dominant,
        "weakest": weakest,
        "balance": balance,
        "balance_detail": balance_detail,
        "growth_edge": growth_edge,
        "preview_text": preview_text,
        "pillars": {
            "year": f"{TIANGAN[ys]}{DIZHI[yb]}",
            "month": f"{TIANGAN[ms]}{DIZHI[mb]}",
            "day": f"{TIANGAN[ds]}{DIZHI[db]}",
            "hour": f"{TIANGAN[hs]}{DIZHI[hb]}",
        }
    }

# ── Email Sending ──────────────────────────────────────────────────────

def send_preview_email(to_email, to_name, preview_data):
    """Send preview email via Resend API."""
    if not RESEND_API_KEY:
        return {"sent": False, "error": "RESEND_API_KEY not configured"}

    preview = preview_data["preview_text"]
    day_master = preview_data["day_master"]
    wuxing = preview_data["day_master_wuxing"]

    html_body = f"""<!DOCTYPE html>
<html><body style="font-family:Georgia,serif;background:#0a0c14;color:#c8ccd6;padding:40px 20px">
<div style="max-width:560px;margin:0 auto;background:#111520;border:1px solid #1e2433;border-radius:12px;padding:32px">
<div style="text-align:center;margin-bottom:24px">
  <div style="font-size:32px">☯</div>
  <h1 style="color:#e8ecf1;font-size:22px;margin:12px 0 4px">Your Energy Blueprint Preview</h1>
  <p style="color:#6b7280;font-size:13px">Prepared for <strong style="color:#c9a96e">{to_name}</strong></p>
</div>
<div style="background:#0a0c14;border:1px solid #1e2433;border-radius:8px;padding:20px;margin:20px 0">
  <p style="color:#c9a96e;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px">Your Day Master</p>
  <h2 style="color:#e8ecf1;font-size:30px;margin:0 0 8px">{day_master} <span style="color:#c9a96e;font-size:18px">({wuxing})</span></h2>
  <p style="color:#8b7348;font-size:14px;margin:0">{preview_data['archetype']}</p>
</div>
<div style="line-height:1.7;font-size:14px;color:#b8b2cc">
  {preview.replace(chr(10), '<br>')}
</div>
<div style="text-align:center;margin:28px 0">
  <a href="https://metaphysics-landing.vercel.app" style="display:inline-block;background:#c9a96e;color:#0a0c14;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px">Unlock Your Full Blueprint →</a>
</div>
<div style="border-top:1px solid #1e2433;padding-top:16px;margin-top:24px">
  <p style="font-size:11px;color:#5c5770;text-align:center">Destiny Code — Your Personal Energy Blueprint<br>This is a one-time preview. No spam, no subscription.</p>
</div>
</div></body></html>"""

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": to_email,
                "subject": f"{to_name}, your Destiny Code preview is ready ✦",
                "html": html_body,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return {"sent": True, "id": resp.json().get("id", "")}
        else:
            return {"sent": False, "error": resp.text[:200]}
    except Exception as e:
        return {"sent": False, "error": str(e)}

NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", FROM_EMAIL)


def send_owner_notification(name, birthdate, birthplace="", birthtime=""):
    """Send a notification email to the site owner via Resend."""
    if not RESEND_API_KEY:
        return {"sent": False, "error": "RESEND_API_KEY not configured"}

    detail_parts = [f"born {birthdate}"]
    if birthtime:
        detail_parts.append(f"at {birthtime}")
    if birthplace:
        detail_parts.append(f"in {birthplace}")
    detail = ", ".join(detail_parts)

    subject = f"New Destiny Code submission from {name}"
    html_body = f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f8f9fa;padding:24px">
<div style="max-width:480px;margin:0 auto;background:#fff;border:1px solid #dee2e6;border-radius:8px;padding:24px">
  <h2 style="color:#212529;margin:0 0 8px">New Destiny Code Submission</h2>
  <p style="color:#6c757d;margin:0 0 16px">{name} just submitted their birth information.</p>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <tr><td style="padding:8px 0;color:#6c757d">Name</td><td style="padding:8px 0;color:#212529;font-weight:600">{name}</td></tr>
    <tr><td style="padding:8px 0;color:#6c757d">Birth Date</td><td style="padding:8px 0;color:#212529;font-weight:600">{birthdate}</td></tr>
    <tr><td style="padding:8px 0;color:#6c757d">Birth Time</td><td style="padding:8px 0;color:#212529;font-weight:600">{birthtime or "—"}</td></tr>
    <tr><td style="padding:8px 0;color:#6c757d">Birth Place</td><td style="padding:8px 0;color:#212529;font-weight:600">{birthplace or "—"}</td></tr>
  </table>
  <p style="font-size:12px;color:#adb5bd;margin:20px 0 0">Destiny Code — automated notification</p>
</div></body></html>"""

    text_body = (
        f"New Destiny Code submission from {name}, {detail}.\n\n"
        f"Name: {name}\n"
        f"Birth Date: {birthdate}\n"
        f"Birth Time: {birthtime or '—'}\n"
        f"Birth Place: {birthplace or '—'}\n"
    )

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": NOTIFY_EMAIL,
                "subject": subject,
                "html": html_body,
                "text": text_body,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return {"sent": True, "id": resp.json().get("id", "")}
        else:
            return {"sent": False, "error": resp.text[:200]}
    except Exception as e:
        return {"sent": False, "error": str(e)}


# ── Vercel Handler ─────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle Formspree webhook POST."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        # Extract form fields (Formspree sends them in various formats)
        name = data.get("name", data.get("Full Name", "")).strip()
        email = data.get("email", data.get("Email Address", "")).strip()
        birthdate = data.get("birthdate", data.get("Birth Date", "")).strip()
        birthtime = data.get("birthtime", data.get("Birth Time", "12:00")).strip()
        birthplace = data.get("birthplace", data.get("Birth Place", "")).strip()

        if not name or not birthdate:
            self._respond(400, {"error": "Missing required fields: name, birthdate"})
            return

        # Parse birth date and time
        try:
            parts = birthdate.split("-")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            self._respond(400, {"error": "Invalid birthdate format. Use YYYY-MM-DD."})
            return

        hour = 12
        if birthtime:
            try:
                time_parts = birthtime.split(":")
                hour = int(time_parts[0])
            except (ValueError, IndexError):
                pass

        # Compute chart
        try:
            result = compute_chart(year, month, day, hour)
        except Exception as e:
            self._respond(500, {"error": f"Chart computation failed: {str(e)}"})
            return

        # Send email only if email address was provided
        email_result = {"sent": False, "error": "No email provided"}
        if email:
            email_result = send_preview_email(email, name, result)

        # Notify site owner (non-blocking — won't affect user response)
        notify_result = send_owner_notification(name, birthdate, birthplace, birthtime)

        self._respond(200, {
            "ok": True,
            "day_master": result["day_master"],
            "day_master_wuxing": result["day_master_wuxing"],
            "dominant": result["dominant"],
            "balance": result["balance"],
            "email_sent": email_result["sent"],
        })

    def do_GET(self):
        """Health check."""
        self._respond(200, {"status": "ok", "service": "Destiny Code Preview API"})

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
