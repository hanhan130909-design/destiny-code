"""
Vercel API — Create Lemon Squeezy Checkout
POST /api/create-checkout
Body: {name, birthdate, birthtime}
Returns: {url: "https://..."}
"""
import os, json
from http.server import BaseHTTPRequestHandler

LEMONSQUEEZY_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")
STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID", "94d59cef-dbb8-4ea5-b178-d2540fcd6919")
VARIANT_ID = os.environ.get("LEMONSQUEEZY_VARIANT_ID", "")
BASE_URL = "https://metaphysics-landing.vercel.app"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        name = data.get("name", "Friend")
        birthdate = data.get("birthdate", "")
        birthtime = data.get("birthtime", "12:00")

        if not birthdate:
            self._respond(400, {"error": "birthdate is required"})
            return
        if not VARIANT_ID:
            self._respond(500, {"error": "Variant not configured"})
            return

        date_parts = birthdate.split("-")
        time_parts = (birthtime or "12:00").split(":")
        report_params = (
            f"name={self._qs(name)}"
            f"&year={date_parts[0]}"
            f"&month={date_parts[1]}"
            f"&day={date_parts[2]}"
            f"&hour={time_parts[0]}"
        )

        import urllib.request

        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "product_options": {
                        "redirect_url": f"{BASE_URL}/report?checkout_id={{CHECKOUT_ID}}&{report_params}",
                        "description": f"Complete Energy Blueprint for {name}",
                    },
                    "checkout_data": {
                        "custom": {
                            "name": name,
                            "birthdate": birthdate,
                            "birthtime": birthtime,
                        }
                    },
                },
                "relationships": {
                    "store": {"data": {"type": "stores", "id": STORE_ID}},
                    "variant": {"data": {"type": "variants", "id": VARIANT_ID}},
                },
            }
        }

        try:
            req = urllib.request.Request(
                "https://api.lemonsqueezy.com/v1/checkouts",
                data=json.dumps(payload).encode(),
                headers={
                    "Authorization": f"Bearer {LEMONSQUEEZY_KEY}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
            checkout_url = result.get("data", {}).get("attributes", {}).get("url", "")
            checkout_id = result.get("data", {}).get("id", "")
            self._respond(200, {"url": checkout_url, "checkout_id": checkout_id})
        except urllib.error.HTTPError as e:
            self._respond(e.code, {"error": e.read().decode()[:500]})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def do_OPTIONS(self):
        self._cors_only()

    def _respond(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _cors_only(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    @staticmethod
    def _qs(s):
        from urllib.parse import quote
        return quote(str(s), safe="")
