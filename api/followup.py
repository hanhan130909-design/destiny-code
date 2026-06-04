"""
Vercel Cron Endpoint — Email Follow-Up Sequence
Runs daily via Vercel Cron Job (or external cron).
Sends follow-up emails to free preview users at 24h and 72h after signup.

GET /api/followup?key=DESTINY_CRON_KEY → process all pending follow-ups
"""
import os
import json
import shelve
import requests
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "Destiny Code <onboarding@resend.dev>")
CRON_KEY = os.environ.get("DESTINY_CRON_KEY", "cron-secret-2026")
FOLLOWUP_DB = "/tmp/followup_db"
SUBMISSIONS_DB = "/tmp/submissions_db"


def _read_all(db_path):
    try:
        with shelve.open(db_path, flag="r") as db:
            return db.get("submissions", [])
    except Exception:
        return []


def _read_followups():
    try:
        with shelve.open(FOLLOWUP_DB, flag="r") as db:
            return db.get("sent", {})
    except Exception:
        return {}


def _save_followups(data):
    try:
        with shelve.open(FOLLOWUP_DB, flag="c") as db:
            db["sent"] = data
    except Exception:
        pass


def _now():
    return datetime.now(timezone.utc)


# ── Follow-Up Email Templates ──────────────────────────────────────

EMAIL_24H = """<!DOCTYPE html>
<html><body style="font-family:Georgia,serif;background:#0a0c14;color:#c8ccd6;padding:40px 20px">
<div style="max-width:560px;margin:0 auto;background:#111520;border:1px solid #1e2433;border-radius:12px;padding:32px">
<div style="text-align:center;margin-bottom:24px">
  <div style="font-size:32px">☯</div>
  <h1 style="color:#e8ecf1;font-size:22px;margin:12px 0 4px">Your energy blueprint holds more than you think</h1>
  <p style="color:#6b7280;font-size:13px">A deeper layer of your {name}'s chart, decoded</p>
</div>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
Hi {name},
</p>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
Since you received your BaZi preview, something interesting has been sitting in your chart — a pattern that affects how others perceive your <strong style="color:#c9a96e">{day_master}</strong> nature.
</p>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
Your Day Master doesn't exist in isolation. The <strong style="color:{accent_color}">Four Pillars</strong> — Year, Month, Day, and Hour — interact like a conversation. What you saw in your preview was just one voice in that conversation.
</p>

<div style="background:#0a0c14;border:1px solid #1e2433;border-radius:8px;padding:20px;margin:24px 0">
  <p style="color:#c9a96e;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">What the Full Blueprint Reveals</p>
  <ul style="list-style:none;padding:0;margin:0">
    <li style="padding:10px 0;border-bottom:1px solid #1e2433;font-size:14px;color:#c8ccd6">◈ <strong style="color:#d8dce3">Career Path</strong> — which industries your elemental makeup naturally amplifies</li>
    <li style="padding:10px 0;border-bottom:1px solid #1e2433;font-size:14px;color:#c8ccd6">◈ <strong style="color:#d8dce3">Wealth Channels</strong> — how your chart patterns money flow and abundance</li>
    <li style="padding:10px 0;border-bottom:1px solid #1e2433;font-size:14px;color:#c8ccd6">◈ <strong style="color:#d8dce3">Relationship Dynamics</strong> — the element balance that shapes your connections</li>
    <li style="padding:10px 0;font-size:14px;color:#c8ccd6">◈ <strong style="color:#d8dce3">12-Month Forecast</strong> — the luck cycles and life chapters ahead</li>
  </ul>
</div>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
Your preview scratched the surface. The full blueprint is an 800+ word deep interpretation — your complete personality matrix, material abundance channels, and the timing of your life chapters.
</p>

<div style="text-align:center;margin:28px 0">
  <a href="https://metaphysics-landing.vercel.app/report?name={name_encoded}&year={year}&month={month}&day={day}&hour={hour}"
     style="display:inline-block;background:#c9a96e;color:#0a0c14;padding:14px 36px;border-radius:6px;text-decoration:none;font-weight:600;font-size:15px">
    Unlock Your Complete Blueprint — $29 →
  </a>
  <p style="font-size:12px;color:#5c5770;margin-top:10px">One-time purchase. Instant delivery. No subscription.</p>
</div>

<div style="border-top:1px solid #1e2433;padding-top:16px;margin-top:24px">
  <p style="font-size:11px;color:#5c5770;text-align:center">Destiny Code — Your Personal Energy Blueprint</p>
</div>
</div></body></html>"""

EMAIL_72H = """<!DOCTYPE html>
<html><body style="font-family:Georgia,serif;background:#0a0c14;color:#c8ccd6;padding:40px 20px">
<div style="max-width:560px;margin:0 auto;background:#111520;border:1px solid #1e2433;border-radius:12px;padding:32px">
<div style="text-align:center;margin-bottom:24px">
  <div style="font-size:32px">✦</div>
  <h1 style="color:#e8ecf1;font-size:22px;margin:12px 0 4px">One last thing about your {day_master} energy</h1>
  <p style="color:#6b7280;font-size:13px">A final note before this preview expires</p>
</div>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
{name} —
</p>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
There is a concept in BaZi called <strong style="color:#c9a96e">Useful God (Yong Shen)</strong> — the element that brings your chart into balance. For someone with your {day_master} Day Master and {dominant}-dominant profile, your Useful God reveals exactly where your natural advantage lies and what you need more of.
</p>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
Most people go through life fighting their own elemental makeup. They push where they should yield. They chase what their chart was never designed to catch. The full blueprint shows you where to aim.
</p>

<div style="background:#0a0c14;border:1px solid #1e2433;border-radius:8px;padding:20px;margin:24px 0">
  <p style="color:#c9a96e;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Your Growth Edge</p>
  <p style="font-size:14px;color:#b8b2cc;line-height:1.7;margin:0">{growth_edge}</p>
</div>

<p style="font-size:15px;line-height:1.8;color:#c8ccd6;margin-bottom:16px">
This is the kind of insight the full report delivers across every life domain — career, wealth, relationships, and timing. 800+ words of personalized interpretation.
</p>

<div style="text-align:center;margin:28px 0">
  <a href="https://metaphysics-landing.vercel.app/report?name={name_encoded}&year={year}&month={month}&day={day}&hour={hour}"
     style="display:inline-block;background:#c9a96e;color:#0a0c14;padding:14px 36px;border-radius:6px;text-decoration:none;font-weight:600;font-size:15px">
    Get Your Complete Blueprint — $29 →
  </a>
  <p style="font-size:12px;color:#5c5770;margin-top:10px">Last chance — preview expires in 24 hours.</p>
</div>

<div style="border-top:1px solid #1e2433;padding-top:16px;margin-top:24px">
  <p style="font-size:11px;color:#5c5770;text-align:center">Destiny Code — Your Personal Energy Blueprint<br>You can unsubscribe anytime.</p>
</div>
</div></body></html>"""


def send_followup(to_email, to_name, subject, html_body):
    """Send follow-up email via Resend."""
    if not RESEND_API_KEY:
        return {"sent": False, "error": "No API key"}

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
                "subject": subject,
                "html": html_body,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return {"sent": True, "id": resp.json().get("id", "")}
        return {"sent": False, "error": resp.text[:200]}
    except Exception as e:
        return {"sent": False, "error": str(e)}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Auth check
        key = self.headers.get("x-cron-key", "")
        if key != CRON_KEY:
            self._respond(401, {"error": "Unauthorized"})
            return

        now = _now()
        submissions = _read_all(SUBMISSIONS_DB)
        sent = _read_followups()
        results = {"processed": 0, "sent_24h": 0, "sent_72h": 0, "skipped": 0}

        for i, sub in enumerate(submissions):
            # Skip if no email
            user_email = sub.get("email", "").strip()
            if not user_email:
                continue

            # Parse submission date
            sub_date_str = sub.get("date", "")
            try:
                sub_date = datetime.fromisoformat(sub_date_str)
            except Exception:
                continue

            hours_ago = (now - sub_date).total_seconds() / 3600
            sub_key = f"{i}_{sub_date_str}"

            # Skip if already sent for this interval
            sent_status = sent.get(sub_key, "")

            user_name = sub.get("name", "Friend")
            birthdate = sub.get("birthdate", "")
            birthtime = sub.get("birthtime", "12:00")

            # Parse birth date for report URL
            year = month = day = hour = 0
            try:
                parts = birthdate.split("-")
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            except Exception:
                pass
            try:
                hour = int(birthtime.split(":")[0])
            except Exception:
                pass

            import urllib.parse
            name_enc = urllib.parse.quote(user_name)

            # Compute basic day master info for email personalization
            # Use a simple mapping based on birth year stem
            day_master_map = {
                0: "Jia", 1: "Yi", 2: "Bing", 3: "Ding",
                4: "Wu", 5: "Ji", 6: "Geng", 7: "Xin",
                8: "Ren", 9: "Gui"
            }
            # Simplified day master from the full algorithm
            dm_idx = ((year - 1900) * 365 + (month - 1) * 30 + day) % 10
            day_master = day_master_map.get(dm_idx, "Unknown")
            accent_color = "#c9a96e"
            dominant = "Fire"  # Simplified
            growth_edge = "Understanding your energy patterns is the first step toward growth."

            # ── 24h Follow-Up ──
            if 23 <= hours_ago <= 30 and "24h" not in sent_status:
                subject = f"{user_name}, your Destiny Code blueprint has a deeper layer"
                body = EMAIL_24H.format(
                    name=user_name,
                    name_encoded=name_enc,
                    day_master=day_master,
                    accent_color=accent_color,
                    year=year, month=month, day=day, hour=hour
                )
                result = send_followup(user_email, user_name, subject, body)
                if result["sent"]:
                    sent[sub_key] = sent_status + ",24h"
                    results["sent_24h"] += 1
                    results["processed"] += 1

            # ── 72h Follow-Up ──
            if 70 <= hours_ago <= 80 and "72h" not in sent_status:
                subject = f"Final note: your {day_master} energy, decoded"
                body = EMAIL_72H.format(
                    name=user_name,
                    name_encoded=name_enc,
                    day_master=day_master,
                    dominant=dominant,
                    growth_edge=growth_edge,
                    year=year, month=month, day=day, hour=hour
                )
                result = send_followup(user_email, user_name, subject, body)
                if result["sent"]:
                    sent[sub_key] = sent_status + ",72h"
                    results["sent_72h"] += 1
                    results["processed"] += 1

            if "24h" in sent_status or "72h" in sent_status:
                results["skipped"] += 1

        _save_followups(sent)
        self._respond(200, results)

    def _respond(self, status_code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
