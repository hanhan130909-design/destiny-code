"""
Destiny Code — AI Interpretation API
Vercel Serverless Function

POST /api/interpret
{
  "name": "string",
  "chart_data": { ... full BaZi chart from /api/preview ... }
}
"""
import os
import json
import sys
from http.server import BaseHTTPRequestHandler
import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

SYSTEM_PROMPT = """You are the Destiny Code Interpreter — a warm, precise, and empowering BaZi (Eight Characters / Four Pillars of Destiny) reader. You translate ancient Chinese elemental wisdom into a modern "Personal Energy Blueprint" for a Western, spiritually-curious audience. You are a mirror, not a fortune-teller.

CRITICAL CONSTRAINTS:
1. No fear language: never say "bad luck", "disaster", "misfortune", "curse", "danger", "warning", "threat".
2. No specific predictions: never predict death, accidents, illness, financial ruin, or exact dates.
3. Reframe all challenges positively: "growth edge" not "weakness", "life curriculum" not "problem".
4. No religious language: no God, Buddha, sin, karma. Use: universe, cosmic rhythm, life force, natural flow.
5. Affirm agency: BaZi reveals tendencies only — the individual always has choice.

OUTPUT: Generate a warm, personal report in 7 sections (500-800 words total):
1. Cosmic Signature (~80 words): Greeting with name, Day Master element + archetype. Make them feel seen.
2. Elemental Landscape (~100 words): Walk through five elements distribution. Connect to life dimensions.
3. Personality Architecture (~200 words): Day Master personality + key traits. Use Ten Gods where relevant.
4. Life's Curriculum (~100 words): 1-2 key life themes as "soul invitations". What mastery looks like.
5. Mirror of Relationships (~100 words): Natural relational style + growth edge. Gender-inclusive.
6. Vocational Compass (~100 words): 2-3 career directions aligned with their elements.
7. Integration (~80 words): Warm summary + one practical experiment for the week.

End with: "Your Energy Blueprint is a mirror — it reflects your innate patterns so you can partner with them consciously. The ancient sages said: know your chart, then transcend it."

Day Master archetypes:
Jia Wood Yang — the towering tree, pioneer. Yi Wood Yin — the resilient vine. Bing Fire Yang — the sun. Ding Fire Yin — the candle flame. Wu Earth Yang — the mountain. Ji Earth Yin — the fertile soil. Geng Metal Yang — the sword. Xin Metal Yin — the jewel. Ren Water Yang — the ocean. Gui Water Yin — the mist."""


def generate_ai_interpretation(chart_data: dict, name: str) -> str:
    """Generate AI interpretation using DeepSeek API."""
    if not DEEPSEEK_API_KEY:
        return ""

    pillars = chart_data.get("pillars", {})
    elements = chart_data.get("elements", {})

    chart_json = {
        "name": name,
        "chart": {
            "yearPillar": {"stem": pillars.get("year", ""), "branch": pillars.get("year", ""), "hiddenStems": []},
            "monthPillar": {"stem": pillars.get("month", ""), "branch": pillars.get("month", ""), "hiddenStems": []},
            "dayPillar": {"stem": pillars.get("day", ""), "branch": pillars.get("day", ""), "hiddenStems": []},
            "hourPillar": {"stem": pillars.get("hour", ""), "branch": pillars.get("hour", ""), "hiddenStems": []},
        },
        "dayMaster": {
            "stem": chart_data.get("day_master", ""),
            "element": chart_data.get("day_master_wuxing", ""),
            "polarity": chart_data.get("day_master_yinyang", ""),
        },
        "fiveElementsBalance": elements,
        "dayMasterStrength": "Balanced",
        "usefulGods": [chart_data.get("dominant", "")],
        "annoyingGods": [chart_data.get("weakest", "")],
    }

    user_prompt = f"""Interpret this BaZi chart for {name}:

```json
{json.dumps(chart_json, indent=2, ensure_ascii=False)}
```

Generate a complete Energy Blueprint report following the 7-section structure. Make it personal, warm, and address {name} directly."""

    try:
        resp = requests.post(
            f"{DEEPSEEK_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=25,
        )
        if resp.status_code == 200:
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        else:
            print(f"DeepSeek API error: {resp.status_code} {resp.text[:300]}", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"DeepSeek API exception: {e}", file=sys.stderr)
        return ""


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
            return

        name = (data.get("name") or "").strip()
        chart_data = data.get("chart_data") or {}

        if not name:
            self._respond(400, {"error": "Missing name"})
            return

        if not chart_data:
            self._respond(400, {"error": "Missing chart_data"})
            return

        if not DEEPSEEK_API_KEY:
            self._respond(200, {"ok": True, "interpretation": "", "error": "AI key not configured"})
            return

        try:
            ai_text = generate_ai_interpretation(chart_data, name)
            self._respond(200, {"ok": True, "interpretation": ai_text})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def do_GET(self):
        self._respond(200, {"status": "ok", "service": "Destiny Code AI Interpretation API"})

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
