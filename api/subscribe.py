"""
Vercel Serverless — Newsletter Subscribe API
POST /api/subscribe → save email to GitHub subscribers list
GET /api/subscribe → return subscriber count
"""
import os, json, requests
from http.server import BaseHTTPRequestHandler
from api.github_db import _get_file, _put_file

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        email = body.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            self._respond(400, {"ok": False, "error": "Invalid email"})
            return
        
        subs = read_subscribers()
        if any(s.get('email') == email for s in subs):
            self._respond(200, {"ok": True, "message": "Already subscribed"})
            return
        
        subs.append({
            "email": email,
            "subscribed_at": __import__('datetime').datetime.utcnow().isoformat(),
            "source": "newsletter_page",
            "active": True
        })
        save_subscribers(subs)
        
        # Send welcome email via Resend
        self._send_welcome(email)
        
        self._respond(200, {"ok": True, "count": len(subs)})
    
    def do_GET(self):
        subs = read_subscribers()
        active = [s for s in subs if s.get('active', True)]
        self._respond(200, {"count": len(active), "subscribers": active})
    
    def _send_welcome(self, email):
        try:
            RESEND = os.environ.get("RESEND_API_KEY", "")
            if not RESEND:
                return
            requests.post("https://api.resend.com/emails", headers={
                "Authorization": f"Bearer {RESEND}",
                "Content-Type": "application/json"
            }, json={
                "from": os.environ.get("FROM_EMAIL", "Destiny Code <onboarding@resend.dev>"),
                "to": email,
                "subject": "Welcome to Destiny Code — Your Energy Blueprint Awaits",
                "html": WELCOME_HTML
            }, timeout=10)
        except:
            pass
    
    def _respond(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

WELCOME_HTML = """<!DOCTYPE html>
<html><body style="font-family:Georgia,serif;background:#0a0c14;color:#c8ccd6;padding:40px 20px">
<div style="max-width:560px;margin:0 auto;background:#111520;border:1px solid #1e2433;border-radius:12px;padding:32px">
<div style="text-align:center;margin-bottom:24px">
  <div style="font-size:36px">☯</div>
  <h1 style="color:#e8ecf1;font-size:22px;margin:12px 0 4px">Welcome to Destiny Code</h1>
  <p style="color:#6b7280;font-size:13px">Your weekly energy forecast starts now</p>
</div>
<p style="font-size:15px;line-height:1.8;color:#c8ccd6">Hey there,</p>
<p style="font-size:15px;line-height:1.8;color:#c8ccd6">You just joined a growing group of people discovering that their birth moment isn't random — it's a precise energy configuration that shapes personality, career, and life timing.</p>
<div style="background:#0a0c14;border:1px solid #1e2433;border-radius:8px;padding:20px;margin:24px 0">
  <p style="color:#c9a96e;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">What you'll get</p>
  <p style="font-size:14px;color:#c8ccd6;margin:0">📅 <strong>Mondays:</strong> Weekly Energy Forecast<br>🔍 <strong>Wednesdays:</strong> Elemental Deep Dives<br>💡 <strong>Fridays:</strong> Practical Guides + Q&A</p>
</div>
<p style="font-size:15px;line-height:1.8;color:#c8ccd6"><strong>Start now:</strong> <a href="https://metaphysics-landing.vercel.app/free-bazi-calculator" style="color:#c9a96e">Get your free Day Master preview →</a> (30 seconds, no email needed)</p>
<p style="font-size:15px;line-height:1.8;color:#c8ccd6">Welcome aboard.</p>
<p style="font-size:15px;color:#c9a96e">☯ Destiny Code</p>
<div style="border-top:1px solid #1e2433;padding-top:16px;margin-top:24px">
  <p style="font-size:11px;color:#5c5770;text-align:center">Destiny Code — Your Personal Energy Blueprint<br>Unsubscribe anytime.</p>
</div>
</div></body></html>"""

# Subscriber helpers
def read_subscribers():
    try:
        result, sha = _get_file("subscribers.json")
        return result if result else []
    except:
        return []

def save_subscribers(subs):
    existing, sha = _get_file("subscribers.json")
    _put_file("subscribers.json", subs, sha if existing else "")
