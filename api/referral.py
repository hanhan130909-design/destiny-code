"""
Destiny Code — Referral / Viral Growth API
POST /api/referral — generate referral code
POST /api/referral/convert — track referral conversion
GET  /api/referral/stats — K-factor & referral stats (admin)
"""
import os
import json
import hashlib
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from http.server import BaseHTTPRequestHandler
from api.github_db import _get_file, _put_file

REFERRALS_FILE = "referrals.json"
BASE_URL = "https://metaphysics-landing.vercel.app/free-bazi-calculator"


def _generate_code(email: str) -> str:
    """Generate a short referral code from email hash."""
    h = hashlib.sha256(email.lower().strip().encode()).hexdigest()[:8]
    return h


def _read_referrals():
    data, sha = _get_file(REFERRALS_FILE)
    if data is None:
        data = {"referrals": [], "stats": {"total_sent": 0, "total_clicks": 0, "total_conversions": 0, "total_revenue": 0}}
    return data, sha


def _save_referrals(data, sha=""):
    return _put_file(REFERRALS_FILE, data, sha)


def create_referral(email: str, name: str = "", day_master: str = "", element: str = ""):
    """Create or retrieve a referral code for a user."""
    code = _generate_code(email)
    data, sha = _read_referrals()

    # Check if this user already has a referral
    for ref in data["referrals"]:
        if ref.get("referrer_email") == email:
            return {
                "code": ref["code"],
                "share_url": f"{BASE_URL}?ref={ref['code']}",
                "share_text": f"My BaZi Day Master is {ref.get('day_master', '?')} ({ref.get('element', '?')}). Discover your cosmic blueprint for free → {BASE_URL}?ref={ref['code']} #BaZi #DestinyCode",
                "existing": True,
            }

    # Create new referral entry
    entry = {
        "code": code,
        "referrer_email": email,
        "referrer_name": name,
        "day_master": day_master,
        "element": element,
        "conversions": 0,
        "clicks": 0,
        "created_at": "",  # will be filled by server timestamp
    }
    data["referrals"].append(entry)
    if len(data["referrals"]) > 500:
        data["referrals"] = data["referrals"][-500:]

    _save_referrals(data, sha)

    return {
        "code": code,
        "share_url": f"{BASE_URL}?ref={code}",
        "share_text": f"My BaZi Day Master is {day_master} ({element}). Discover your cosmic blueprint for free → {BASE_URL}?ref={code} #BaZi #DestinyCode",
        "existing": False,
    }


def track_click(code: str):
    """Track a referral link click."""
    data, sha = _read_referrals()
    for ref in data["referrals"]:
        if ref["code"] == code:
            ref["clicks"] = ref.get("clicks", 0) + 1
            data["stats"]["total_clicks"] = data["stats"].get("total_clicks", 0) + 1
            _save_referrals(data, sha)
            return {"tracked": True, "code": code}
    return {"tracked": False, "error": "Invalid referral code"}


def track_conversion(code: str, referred_email: str):
    """Track a referral conversion (someone signed up/computed)."""
    data, sha = _read_referrals()
    for ref in data["referrals"]:
        if ref["code"] == code:
            ref["conversions"] = ref.get("conversions", 0) + 1
            data["stats"]["total_conversions"] = data["stats"].get("total_conversions", 0) + 1
            data["stats"]["total_revenue"] = data["stats"].get("total_revenue", 0) + 29  # estimate
            _save_referrals(data, sha)
            return {
                "tracked": True,
                "code": code,
                "referrer_email": ref["referrer_email"],
                "reward": "$5 off for both parties",
            }
    return {"tracked": False, "error": "Invalid referral code"}


def get_kfactor():
    """Calculate viral coefficient and referral stats."""
    data, _ = _read_referrals()
    stats = data.get("stats", {})
    total_users = stats.get("total_users", 0)
    total_conversions = stats.get("total_conversions", 0)
    total_clicks = stats.get("total_clicks", 0)

    # K-factor = average # of new users each existing user brings
    if total_users > 0:
        k_factor = round(total_conversions / total_users, 3)
    else:
        k_factor = 0.0

    # Conversion rate from click → signup
    if total_clicks > 0:
        click_to_signup = round(total_conversions / total_clicks * 100, 1)
    else:
        click_to_signup = 0.0

    return {
        "k_factor": k_factor,
        "total_referrals": len(data.get("referrals", [])),
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "click_to_signup_pct": click_to_signup,
        "total_revenue": stats.get("total_revenue", 0),
        "target_k_factor": 0.3,
        "status": "viral" if k_factor >= 0.3 else ("growing" if k_factor >= 0.1 else "needs_boost"),
    }


def update_total_users():
    """Increment total user count for K-factor calculation."""
    data, sha = _read_referrals()
    data["stats"]["total_users"] = data["stats"].get("total_users", 0) + 1
    _save_referrals(data, sha)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if "/stats" in self.path:
            # Admin: K-factor stats
            stats = get_kfactor()
            self.wfile.write(json.dumps(stats, indent=2).encode())
        else:
            self.wfile.write(json.dumps({"error": "GET not supported, use POST"}).encode())

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        result = {"error": "Unknown action"}

        if "/convert" in self.path:
            # Track a referral conversion
            code = data.get("code", "")
            email = data.get("email", "")
            result = track_conversion(code, email)

        elif "/click" in self.path:
            # Track a referral link click
            code = data.get("code", "")
            result = track_click(code)

        else:
            # Generate referral code
            email = data.get("email", "")
            name = data.get("name", "")
            day_master = data.get("day_master", "")
            element = data.get("element", "")

            if not email:
                result = {"error": "Email is required"}
            else:
                result = create_referral(email, name, day_master, element)

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
