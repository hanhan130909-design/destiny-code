"""Vercel serverless endpoint: send newsletter edition to all active subscribers."""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import base64

# Vercel Python handler
try:
    from http.server import BaseHTTPRequestHandler
except ImportError:
    pass

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "Destiny Code <onboarding@resend.dev>")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO = "hanhan130909-design/destiny-code"
API_BASE = f"https://api.github.com/repos/{REPO}/contents/data"


def _get_file(filename):
    """Read JSON file from GitHub repo."""
    if not GH_TOKEN:
        return None, ""
    url = f"{API_BASE}/{filename}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "DestinyCode-NL")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data.get("sha", "")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, ""
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def _put_file(filename, data, sha=""):
    """Write JSON file to GitHub repo."""
    if not GH_TOKEN:
        return False
    url = f"{API_BASE}/{filename}"
    content_b64 = base64.b64encode(
        json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("ascii")
    body = {"message": f"Newsletter: update {filename}", "content": content_b64}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(url, method="PUT")
    req.add_header("Authorization", f"Bearer {GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "DestinyCode-NL")
    try:
        data_bytes = json.dumps(body).encode("utf-8")
        with urllib.request.urlopen(req, data=data_bytes, timeout=15) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        print(f"[newsletter_send] _put_file error: {e}")
        return False


def send_email_via_resend(to_email, subject, html_body):
    """Send one email via Resend API."""
    if not RESEND_API_KEY:
        return {"sent": False, "error": "No RESEND_API_KEY"}
    
    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }
    
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        method="POST"
    )
    req.add_header("Authorization", f"Bearer {RESEND_API_KEY}")
    req.add_header("Content-Type", "application/json")
    
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        with urllib.request.urlopen(req, data=data_bytes, timeout=15) as resp:
            result = json.loads(resp.read().decode())
        return {"sent": True, "id": result.get("id", ""), "error": None}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:500]
        return {"sent": False, "error": f"Resend HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"sent": False, "error": str(e)}


# --- Newsletter Content: Edition #1 ---
NEWSLETTER_SUBJECT = "Your personality has a blind spot \u2014 find your missing element"

NEWSLETTER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#0a0c14;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0a0c14;padding:40px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;">

  <!-- Header -->
  <tr>
    <td style="padding:40px 30px 20px;text-align:center;">
      <h1 style="color:#c9a96e;font-size:28px;margin:0 0 8px;font-weight:300;letter-spacing:2px;">DESTINY CODE</h1>
      <p style="color:#6a6f7d;font-size:13px;margin:0;letter-spacing:1px;">WEEKLY NEWSLETTER \u2014 EDITION #1</p>
    </td>
  </tr>

  <!-- Divider -->
  <tr>
    <td style="padding:0 30px;">
      <hr style="border:none;border-top:1px solid #c9a96e;opacity:0.3;">
    </td>
  </tr>

  <!-- Title -->
  <tr>
    <td style="padding:30px 30px 8px;">
      <h2 style="color:#c9a96e;font-size:24px;margin:0;font-weight:400;line-height:1.3;">
        The Element You're Missing
      </h2>
    </td>
  </tr>

  <!-- Body -->
  <tr>
    <td style="padding:20px 30px;color:#c8ccd6;font-size:15px;line-height:1.7;">

      <p>Hi there,</p>

      <p>You know your zodiac sign. Maybe you've even looked up your Chinese zodiac animal. But there's a deeper layer most people never discover \u2014 and it's hiding in plain sight inside your birth chart.</p>

      <p style="color:#c9a96e;font-weight:500;font-size:17px;">The Five Elements aren't just philosophy. They're a map of your personality's operating system.</p>

      <p>Wood, Fire, Earth, Metal, Water. In BaZi (Four Pillars of Destiny), every person has a unique elemental blueprint. When one of these elements is <em>missing</em> from your chart, it creates a blind spot you may not even know you have.</p>

      <p><strong>Here's what happens when you're missing an element:</strong></p>

      <table width="100%" cellpadding="12" cellspacing="0" style="border-collapse:collapse;">
        <tr style="background-color:rgba(201,169,110,0.08);">
          <td style="color:#c9a96e;font-weight:600;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);width:80px;">NO WOOD</td>
          <td style="color:#c8ccd6;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);">Struggle to plan ahead. Reactive instead of strategic. Miss growth opportunities.</td>
        </tr>
        <tr style="background-color:rgba(201,169,110,0.04);">
          <td style="color:#c9a96e;font-weight:600;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);">NO FIRE</td>
          <td style="color:#c8ccd6;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);">Appear cold or unapproachable. Difficulty expressing passion. Others misread you.</td>
        </tr>
        <tr style="background-color:rgba(201,169,110,0.08);">
          <td style="color:#c9a96e;font-weight:600;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);">NO EARTH</td>
          <td style="color:#c8ccd6;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);">Feel ungrounded. Lack stability in relationships. Trust issues with yourself.</td>
        </tr>
        <tr style="background-color:rgba(201,169,110,0.04);">
          <td style="color:#c9a96e;font-weight:600;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);">NO METAL</td>
          <td style="color:#c8ccd6;font-size:14px;border-bottom:1px solid rgba(201,169,110,0.2);">Poor boundaries. Say yes when you mean no. Let others define your worth.</td>
        </tr>
        <tr style="background-color:rgba(201,169,110,0.08);">
          <td style="color:#c9a96e;font-weight:600;font-size:14px;">NO WATER</td>
          <td style="color:#c8ccd6;font-size:14px;">Overthink without insight. Stuck in loops. Wisdom eludes you \u2014 even when it's in front of you.</td>
        </tr>
      </table>

      <p style="margin-top:24px;">I saw this play out with a client recently. She's ambitious, sharp, and runs a successful consulting business. But every three months, she'd burn out and shut down. Her chart was heavy Fire and Wood \u2014 zero Water. She was driving 100 mph with no cooling system.</p>

      <p>Once she understood the gap, everything changed. She added morning rituals (Water's domain), built in reflection time, and stopped fighting her natural rhythm. Six weeks later: her first month without a crash.</p>

      <p style="color:#c9a96e;font-weight:500;font-size:16px;">Your missing element isn't a flaw. It's a compass pointing to your next level of growth.</p>

      <p>Ready to discover yours?</p>

    </td>
  </tr>

  <!-- CTA -->
  <tr>
    <td style="padding:20px 30px 30px;text-align:center;">

      <a href="https://metaphysics-landing.vercel.app/calculator" style="display:inline-block;background-color:#c9a96e;color:#0a0c14;text-decoration:none;padding:14px 40px;border-radius:4px;font-size:16px;font-weight:600;letter-spacing:1px;">
        FREE CALCULATOR \u2192
      </a>

      <p style="color:#6a6f7d;font-size:13px;margin:16px 0 4px;">
        Find your Five Elements balance in 30 seconds \u2014 free
      </p>
      <p style="color:#6a6f7d;font-size:13px;margin:0;">
        Or unlock your <a href="https://metaphysics-landing.vercel.app/report" style="color:#c9a96e;text-decoration:none;">Complete Blueprint</a> for $29
      </p>

    </td>
  </tr>

  <!-- Divider -->
  <tr>
    <td style="padding:0 30px;">
      <hr style="border:none;border-top:1px solid #c9a96e;opacity:0.2;">
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="padding:20px 30px 40px;text-align:center;">
      <p style="color:#4a4f5d;font-size:12px;margin:0;">
        You received this email because you subscribed to the Destiny Code newsletter.
      </p>
      <p style="color:#4a4f5d;font-size:12px;margin:6px 0 0;">
        <a href="https://metaphysics-landing.vercel.app/newsletter" style="color:#6a6f7d;text-decoration:underline;">Manage preferences</a>
        &nbsp;\u00b7&nbsp;
        Destiny Code \u00b7 metaphysics-landing.vercel.app
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """POST /api/newsletter_send — send newsletter to all active subscribers."""
        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length) if content_length else b"{}"
        
        try:
            params = json.loads(body_raw.decode("utf-8"))
        except:
            params = {}
        
        edition = params.get("edition", "1")
        dry_run = params.get("dry_run", False)
        
        # Read subscribers
        subscribers, sha = _get_file("subscribers.json")
        if subscribers is None:
            self._respond(500, {"error": "Cannot read subscribers from GitHub"})
            return
        
        active = [s for s in subscribers if s.get("active", True)]
        
        if not active:
            self._respond(200, {"sent": 0, "message": "No active subscribers", "total": len(subscribers)})
            return
        
        results = []
        if not dry_run:
            for sub in active:
                email = sub.get("email", "")
                result = send_email_via_resend(email, NEWSLETTER_SUBJECT, NEWSLETTER_HTML)
                result["email"] = email
                results.append(result)
                time.sleep(0.3)  # Rate limit
            
            # Update subscribers with edition_sent
            updated = False
            for sub in subscribers:
                if sub.get("active", True):
                    if "editions_sent" not in sub:
                        sub["editions_sent"] = []
                    sub["editions_sent"].append({
                        "edition": edition,
                        "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "subject": NEWSLETTER_SUBJECT
                    })
                    updated = True
            
            if updated:
                _put_file("subscribers.json", subscribers, sha)
        else:
            results = [{"email": s["email"], "sent": False, "note": "dry_run", "error": None} for s in active]
        
        success_count = sum(1 for r in results if r.get("sent"))
        fail_count = len(results) - success_count
        
        self._respond(200, {
            "sent": success_count,
            "failed": fail_count,
            "total": len(results),
            "edition": edition,
            "dry_run": dry_run,
            "results": results,
        })
    
    def do_GET(self):
        """GET /api/newsletter_send — return status (read-only)."""
        subscribers, _ = _get_file("subscribers.json")
        count = len(subscribers) if subscribers else 0
        active_count = len([s for s in (subscribers or []) if s.get("active", True)])
        
        self._respond(200, {
            "status": "ready",
            "subscribers_total": count,
            "subscribers_active": active_count,
            "from_email": FROM_EMAIL,
            "resend_configured": bool(RESEND_API_KEY),
            "gh_configured": bool(GH_TOKEN),
        })
    
    def _respond(self, status_code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
