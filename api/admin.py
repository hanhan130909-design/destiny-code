"""
Vercel Serverless Function — Admin Submissions Proxy

Proxies Formspree submissions API, keeping the API key server-side.
Called by /admin.html after password gate.
"""
import os
import json
import requests
from http.server import BaseHTTPRequestHandler

FORMSPREE_API_KEY = os.environ.get("FORMSPREE_API_KEY", "")
FORM_ID = "mwvzzdgd"
FORMSPREE_URL = f"https://formspree.io/api/0/forms/{FORM_ID}/submissions"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not FORMSPREE_API_KEY:
            self._respond(500, {"error": "FORMSPREE_API_KEY not configured on server"})
            return

        try:
            resp = requests.get(
                FORMSPREE_URL,
                headers={
                    "Authorization": f"Bearer {FORMSPREE_API_KEY}",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                submissions = data.get("submissions", [])
                # Extract relevant fields for display
                simplified = []
                for sub in submissions:
                    fields = sub.get("data", {}) if isinstance(sub.get("data"), dict) else sub
                    simplified.append({
                        "id": sub.get("id", ""),
                        "date": sub.get("created_at", sub.get("_date", "")),
                        "name": fields.get("name", fields.get("Full Name", "Unknown")),
                        "email": fields.get("email", fields.get("Email Address", "")),
                        "birthdate": fields.get("birthdate", fields.get("Birth Date", "")),
                        "birthtime": fields.get("birthtime", fields.get("Birth Time", "")),
                        "birthplace": fields.get("birthplace", fields.get("Birth Place", "")),
                    })
                self._respond(200, {
                    "total": len(simplified),
                    "submissions": simplified,
                })
            else:
                self._respond(resp.status_code, {
                    "error": f"Formspree API returned {resp.status_code}",
                    "detail": resp.text[:500],
                })
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _respond(self, status_code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)
