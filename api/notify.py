"""
Notification module — sends site-owner alerts on form submissions via Resend.

Import and call send_owner_notification() from preview.py after a successful
BaZi chart computation to let the site owner know someone submitted their info.
"""

import os
import requests

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "Destiny Code <onboarding@resend.dev>")
# Where the owner notification is delivered — defaults to FROM_EMAIL if not set
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", FROM_EMAIL)


def send_owner_notification(name, birthdate, birthplace="", birthtime=""):
    """Send a simple notification email to the site owner via Resend.

    Args:
        name: Submitter's full name.
        birthdate: Birth date string (YYYY-MM-DD or similar).
        birthplace: Optional birth place.
        birthtime: Optional birth time.

    Returns:
        dict: {"sent": bool, "id"|"error": str}
    """
    if not RESEND_API_KEY:
        return {"sent": False, "error": "RESEND_API_KEY not configured"}

    detail_parts = [f"born {birthdate}"]
    if birthtime:
        detail_parts.append(f"at {birthtime}")
    if birthplace:
        detail_parts.append(f"in {birthplace}")

    detail = ", ".join(detail_parts)

    subject = f"New Destiny Code submission from {name}"
    html_body = f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f8f9fa;padding:24px">
<div style="max-width:480px;margin:0 auto;background:#fff;border:1px solid #dee2e6;border-radius:8px;padding:24px">
  <h2 style="color:#212529;margin:0 0 8px">New Destiny Code Submission</h2>
  <p style="color:#6c757d;margin:0 0 16px">{name} just submitted their birth information.</p>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <tr><td style="padding:8px 0;color:#6c757d">Name</td><td style="padding:8px 0;color:#212529;font-weight:600">{name}</td></tr>
    <tr><td style="padding:8px 0;color:#6c757d">Birth Date</td><td style="padding:8px 0;color:#212529;font-weight:600">{birthdate}</td></tr>
    <tr><td style="padding:8px 0;color:#6c757d">Birth Time</td><td style="padding:8px 0;color:#212529;font-weight:600">{birthtime or "—"}</td></tr>
    <tr><td style="padding:8px 0;color:#6c757d">Birth Place</td><td style="padding:8px 0;color:#212529;font-weight:600">{birthplace or "—"}</td></tr>
  </table>
  <p style="font-size:12px;color:#adb5bd;margin:20px 0 0">Destiny Code — automated notification</p>
</div></body></html>"""

    text_body = (
        f"New Destiny Code submission from {name}, {detail}.\n\n"
        f"Name: {name}\n"
        f"Birth Date: {birthdate}\n"
        f"Birth Time: {birthtime or '—'}\n"
        f"Birth Place: {birthplace or '—'}\n"
    )

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": NOTIFY_EMAIL,
                "subject": subject,
                "html": html_body,
                "text": text_body,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return {"sent": True, "id": resp.json().get("id", "")}
        else:
            return {"sent": False, "error": resp.text[:200]}
    except Exception as e:
        return {"sent": False, "error": str(e)}
