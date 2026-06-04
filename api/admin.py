"""
Vercel Serverless Function — Admin Submissions

Stores submissions in-memory + /tmp for Vercel warm-instance persistence.
GET  → list all submissions
POST → store new submission (called from index.html form)
"""
import os
import json
import shelve
from http.server import BaseHTTPRequestHandler

DB_PATH = "/tmp/submissions_db"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            submissions = _read_all()
            self._respond(200, {
                "total": len(submissions),
                "submissions": submissions,
            })
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        name = (data.get("name") or "").strip()
        if not name:
            self._respond(400, {"error": "Missing name"})
            return

        entry = {
            "name": name,
            "email": (data.get("email") or "").strip(),
            "birthdate": (data.get("birthdate") or "").strip(),
            "birthtime": (data.get("birthtime") or "").strip(),
            "birthplace": (data.get("birthplace") or "").strip(),
            "date": _now_iso(),
        }
        _append(entry)
        self._respond(200, {"ok": True})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _respond(self, status_code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)


def _read_all():
    """Read all submissions."""
    try:
        with shelve.open(DB_PATH, flag="r") as db:
            return db.get("submissions", [])
    except Exception:
        return []


def _append(entry):
    """Append a submission."""
    submissions = _read_all()
    submissions.append(entry)
    # Keep only last 200 entries
    if len(submissions) > 200:
        submissions = submissions[-200:]
    try:
        with shelve.open(DB_PATH, flag="c") as db:
            db["submissions"] = submissions
    except Exception:
        pass


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
