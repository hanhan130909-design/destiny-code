"""
Vercel API — Verify Lemon Squeezy Checkout & return full report
GET /api/verify-session?checkout_id=xxx&name=...&year=...&month=...&day=...&hour=...

If paid → returns {paid: true, report: {...}}
If not paid → returns {paid: false}
"""
import os, json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

LEMONSQUEEZY_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.report import build_report

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        checkout_id = params.get("checkout_id", [None])[0]

        if checkout_id:
            import urllib.request
            try:
                req = urllib.request.Request(
                    f"https://api.lemonsqueezy.com/v1/checkouts/{checkout_id}",
                    headers={
                        "Authorization": f"Bearer {LEMONSQUEEZY_KEY}",
                        "Accept": "application/vnd.api+json",
                    },
                )
                with urllib.request.urlopen(req) as resp:
                    result = json.loads(resp.read())

                attrs = result.get("data", {}).get("attributes", {})
                status = attrs.get("status", "")

                if status == "paid":
                    custom = attrs.get("checkout_data", {}).get("custom", {})
                    name = custom.get("name") or params.get("name", ["Friend"])[0]
                    birthdate = custom.get("birthdate", "")
                    birthtime = custom.get("birthtime", "12:00")

                    if birthdate:
                        parts = birthdate.split("-")
                        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    else:
                        year = int(params.get("year", [2000])[0])
                        month = int(params.get("month", [1])[0])
                        day = int(params.get("day", [1])[0])

                    hour = int(birthtime.split(":")[0]) if birthtime else int(params.get("hour", ["12"])[0])

                    report = build_report(name, year, month, day, hour)
                    self._respond(200, {"paid": True, "report": report})
                    return
                else:
                    self._respond(200, {"paid": False, "status": status})
                    return
            except urllib.error.HTTPError as e:
                self._respond(200, {"paid": False, "error": f"API error {e.code}"})
                return
            except Exception as e:
                self._respond(200, {"paid": False, "error": str(e)})
                return

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
