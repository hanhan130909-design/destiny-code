"""
Vercel Serverless Function — Lead Magnet API

Accepts an email address and returns a download link for the free PDF guide.
Optionally sends the guide via Resend email if RESEND_API_KEY is configured.
"""

import sys
import os
import json
import requests
from http.server import BaseHTTPRequestHandler

# Resend API key — set in Vercel environment variables
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "Destiny Code <onboarding@resend.dev>")

# URL for the free PDF guide (hosted as a static asset or external link)
PDF_GUIDE_URL = os.environ.get(
    "PDF_GUIDE_URL",
    "https://metaphysics-landing.vercel.app/guides/five-elements-personality.pdf"
)


def send_leadmagnet_email(to_email):
    """Send the free PDF guide download link via Resend."""
    if not RESEND_API_KEY:
        return {"sent": False, "error": "RESEND_API_KEY not configured"}

    html_body = f"""<!DOCTYPE html>
<html><body style="font-family:Georgia,serif;background:#0a0c14;color:#c8ccd6;padding:40px 20px">
<div style="max-width:560px;margin:0 auto;background:#111520;border:1px solid #1e2433;border-radius:12px;padding:32px">
  <div style="text-align:center;margin-bottom:24px">
    <div style="font-size:32px">☯</div>
    <h1 style="color:#e8ecf1;font-size:22px;margin:12px 0 4px">Your Free PDF Guide is Ready</h1>
    <p style="color:#6b7280;font-size:13px">"The 5 Elements & Your Personality"</p>
  </div>
  <div style="background:#0a0c14;border:1px solid #1e2433;border-radius:8px;padding:20px;margin:20px 0;text-align:center">
    <p style="color:#c8ccd6;font-size:14px;line-height:1.7;margin:0 0 20px">
      Discover how the five elements — Wood, Fire, Earth, Metal, and Water —
      shape your personality, relationships, and life path.
    </p>
    <a href="{PDF_GUIDE_URL}"
       style="display:inline-block;background:#c9a96e;color:#0a0c14;padding:14px 36px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px">
      📥 Download Your Free Guide →
    </a>
  </div>
  <div style="border-top:1px solid #1e2433;padding-top:16px;margin-top:24px">
    <p style="font-size:11px;color:#5c5770;text-align:center">
      Destiny Code — Your Personal Energy Blueprint<br>
      This is a one-time email. No spam, no subscription.
    </p>
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
                "subject": "Your Free PDF Guide: The 5 Elements & Your Personality ✦",
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


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Accept email, return download link + optionally send via Resend."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        email = data.get("email", "").strip()

        if not email:
            self._respond(400, {"error": "Email is required"})
            return

        # Simple email validation
        if "@" not in email or "." not in email.split("@")[-1]:
            self._respond(400, {"error": "Please provide a valid email address"})
            return

        # Send the guide via email if Resend is configured
        email_result = send_leadmagnet_email(email)

        self._respond(200, {
            "ok": True,
            "download_url": PDF_GUIDE_URL,
            "email_sent": email_result["sent"],
            "message": "Check your inbox for the download link!",
        })

    def do_GET(self):
        """Health check."""
        self._respond(200, {"status": "ok", "service": "Destiny Code Lead Magnet API"})

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
