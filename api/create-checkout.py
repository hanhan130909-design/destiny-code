"""
Vercel API — Create Stripe Checkout Session
POST /api/create-checkout
Body: {name, email, birthdate, birthtime, birthplace}
Returns: {url: "https://checkout.stripe.com/..."}
"""
import os, json
from http.server import BaseHTTPRequestHandler

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
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
        email = data.get("email", "")
        birthdate = data.get("birthdate", "")
        birthtime = data.get("birthtime", "12:00")

        if not birthdate:
            self._respond(400, {"error": "birthdate is required"})
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

        import stripe
        stripe.api_key = STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Destiny Code — Complete Energy Blueprint",
                            "description": "Personalized 800+ word BaZi interpretation with career, relationships & life chapters guidance.",
                        },
                        "unit_amount": 2900,  # $29.00
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{BASE_URL}/report?session_id={{CHECKOUT_SESSION_ID}}&{report_params}",
                cancel_url=f"{BASE_URL}/",
                metadata={
                    "name": name,
                    "email": email,
                    "birthdate": birthdate,
                    "birthtime": birthtime,
                },
            )
            self._respond(200, {"url": session.url, "session_id": session.id})
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
        """Minimal URL query-string encoding for safe values."""
        from urllib.parse import quote
        return quote(str(s), safe="")
