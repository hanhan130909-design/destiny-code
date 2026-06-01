"""
Vercel API — Verify Stripe Checkout Session & return full report
GET /api/verify-session?session_id=cs_xxx&name=...&year=...&month=...&day=...&hour=...

If paid → returns {paid: true, report: {...}}
If not paid → returns {paid: false}
"""
import os, json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

# Re-use report generation from report.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.report import build_report

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        session_id = params.get("session_id", [None])[0]

        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status == "paid":
                    # Build full report from metadata or query params
                    meta = session.metadata or {}
                    name = meta.get("name") or params.get("name", ["Friend"])[0]
                    year = int(meta.get("birthdate", "").split("-")[0] or params.get("year", [2000])[0])
                    month = int(meta.get("birthdate", "").split("-")[1] or params.get("month", [1])[0])
                    day = int(meta.get("birthdate", "").split("-")[2] or params.get("day", [1])[0])
                    # Hour from metadata birthtime
                    hour_str = meta.get("birthtime", params.get("hour", ["12"])[0])
                    hour = int(hour_str.split(":")[0]) if isinstance(hour_str, str) else int(hour_str)
                    
                    report = build_report(name, year, month, day, hour)
                    self._respond(200, {"paid": True, "report": report})
                    return
                else:
                    self._respond(200, {"paid": False})
                    return
            except Exception as e:
                self._respond(200, {"paid": False, "error": str(e)})
                return

        # No session_id provided
        self._respond(200, {"paid": False})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _respond(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
