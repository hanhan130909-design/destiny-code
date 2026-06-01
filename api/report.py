"""
Vercel API — Full Report generation
GET /api/report?year=1984&month=6&day=15&hour=8&name=Luna
"""
import sys, os, json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Inline BaZi compute — self-contained for Vercel serverless
# (Same logic as api/preview.py, duplicated for deployment isolation)

import datetime

TIANGAN = ["", "Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
TIANGAN_WUXING = ["", "Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]
TIANGAN_YINYANG = ["", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"]
DIZHI = ["", "Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
DIZHI_WUXING = ["", "Water", "Earth", "Wood", "Wood", "Earth", "Fire", "Fire", "Earth", "Metal", "Metal", "Earth", "Water"]
DIZHI_YINYANG = ["", "Yang", "Yin", "Yang", "Yin", "Yang", "Yang", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"]

_REF_DATE = datetime.date(1900, 1, 1)
_REF_STEM = 1
_REF_BRANCH = 11

_STEM_GROUPS = {1:1,6:1,2:2,7:2,3:3,8:3,4:4,9:4,5:5,10:5}

_MONTH_STEM = {
    1:{1:3,2:4,3:5,4:6,5:7,6:8,7:9,8:10,9:1,10:2,11:3,12:4},
    2:{1:5,2:6,3:7,4:8,5:9,6:10,7:1,8:2,9:3,10:4,11:5,12:6},
    3:{1:7,2:8,3:9,4:10,5:1,6:2,7:3,8:4,9:5,10:6,11:7,12:8},
    4:{1:9,2:10,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10},
    5:{1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:1,12:2},
}

_MONTH_BRANCH = {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,12:1}

_HOUR_BRANCH = {23:1,0:1,1:2,3:3,5:4,7:5,9:6,11:7,13:8,15:9,17:10,19:11,21:12}

_HOUR_STEM = {
    1:{1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:1,12:2},
    2:{1:3,2:4,3:5,4:6,5:7,6:8,7:9,8:10,9:1,10:2,11:3,12:4},
    3:{1:5,2:6,3:7,4:8,5:9,6:10,7:1,8:2,9:3,10:4,11:5,12:6},
    4:{1:7,2:8,3:9,4:10,5:1,6:2,7:3,8:4,9:5,10:6,11:7,12:8},
    5:{1:9,2:10,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10},
}

def day_pillar(year, month, day):
    delta = (datetime.date(year, month, day) - _REF_DATE).days
    return ((_REF_STEM - 1 + delta) % 10) + 1, ((_REF_BRANCH - 1 + delta) % 12) + 1

def year_pillar(year, month, day):
    if month < 2 or (month == 2 and day < 4):
        year -= 1
    return ((year - 4) % 10) + 1, ((year - 4) % 12) + 1

def month_pillar(year_stem, month):
    g = _STEM_GROUPS.get(year_stem, 1)
    return _MONTH_STEM[g][month], _MONTH_BRANCH[month]

def hour_pillar(day_stem, hour):
    b = _HOUR_BRANCH.get(hour, 1)
    g = _STEM_GROUPS.get(day_stem, 1)
    return _HOUR_STEM[g][b], b

def compute_chart(year, month, day, hour=0):
    ys, yb = year_pillar(year, month, day)
    ms, mb = month_pillar(ys, month)
    ds, db = day_pillar(year, month, day)
    hs, hb = hour_pillar(ds, hour)

    dm = TIANGAN[ds]
    dw = TIANGAN_WUXING[ds]
    dy = TIANGAN_YINYANG[ds]

    elements = {"Wood":0,"Fire":0,"Earth":0,"Metal":0,"Water":0}
    for s in [ys,ms,ds,hs]: elements[TIANGAN_WUXING[s]] += 1
    for b in [yb,mb,db,hb]: elements[DIZHI_WUXING[b]] += 1

    sel = sorted(elements.items(), key=lambda x: -x[1])
    dominant, weakest = sel[0][0], sel[-1][0]
    mx, mn = sel[0][1], sel[-1][1]

    if mx >= 4:
        balance, bdetail = "strongly dominated", f"Your chart is strongly dominated by {dominant} energy."
    elif mx >= 3 and mn <= 1:
        balance, bdetail = "imbalanced", f"Strong {dominant} with very little {weakest}. Balancing these is a key growth theme."
    elif mx <= 2:
        balance, bdetail = "well-distributed", "Your energies are well-distributed, giving you versatility."
    else:
        balance, bdetail = "moderately balanced", f"Leaning toward {dominant} while maintaining access to all elements."

    DAY_MASTER_ARCHETYPES = {
        ("Jia","Yang"):"the towering tree — pioneer spirit and natural leadership",
        ("Yi","Yin"):"the resilient vine — graceful, adaptable, and quietly unstoppable",
        ("Bing","Yang"):"the sun itself — radiant, generous, and impossible to ignore",
        ("Ding","Yin"):"the candle flame — warm, magnetic, with a light that draws others close",
        ("Wu","Yang"):"the mountain — steady, protective, and immovable when it matters",
        ("Ji","Yin"):"the fertile soil — nurturing, resourceful, the ground where things grow",
        ("Geng","Yang"):"the sword — decisive, principled, with a natural instinct for justice",
        ("Xin","Yin"):"the jewel — refined, discerning, with an eye for what truly matters",
        ("Ren","Yang"):"the ocean — visionary, expansive, carrying depths most never see",
        ("Gui","Yin"):"the mist — subtle, intuitive, a quiet wisdom that permeates everything",
    }
    GROWTH_EDGES = {
        "Jia":"Your forward momentum can overwhelm others — true strength sometimes means pausing.",
        "Yi":"Grace becomes avoidance when overused — sometimes the most elegant path is the direct one.",
        "Bing":"The sun doesn't need to shine at full intensity in every moment to be powerful.",
        "Ding":"Trust that your gentle light is enough — you don't need to burn brighter to matter.",
        "Wu":"The mountain that never shifts becomes isolated from the changing landscape. Learn to bend.",
        "Ji":"Remember to nurture yourself with the same generosity you extend to everyone else.",
        "Geng":"The sword that's too sharp breaks. Truth without care becomes cruelty.",
        "Xin":"Your eye for quality can become a barrier to connection. Perfection is a direction.",
        "Ren":"The ocean's depth can become isolation. Let people sail your waters.",
        "Gui":"Your quiet wisdom needs to find its voice. The mist that never lifts leaves others lost.",
    }
    archetype = DAY_MASTER_ARCHETYPES.get((dm, dy), "a unique and powerful configuration")
    growth_edge = GROWTH_EDGES.get(dm, "Understanding your energy is the first step.")

    return {
        "day_master": dm, "day_master_wuxing": dw, "day_master_yinyang": dy,
        "archetype": archetype, "growth_edge": growth_edge,
        "dominant": dominant, "weakest": weakest, "balance": balance,
        "balance_detail": bdetail, "elements": elements,
        "pillars": {"year": f"{TIANGAN[ys]}{DIZHI[yb]}", "month": f"{TIANGAN[ms]}{DIZHI[mb]}",
                     "day": f"{TIANGAN[ds]}{DIZHI[db]}", "hour": f"{TIANGAN[hs]}{DIZHI[hb]}"},
    }

def build_report(name, year, month, day, hour):
    result = compute_chart(year, month, day, hour)
    dm = result['day_master']
    wuxing = result['day_master_wuxing']
    yinyang = result['day_master_yinyang']
    dm_name = result['archetype']
    dominant = result['dominant']
    weakest = result['weakest']
    growth = result['growth_edge']
    pillars = result['pillars']

    # Personality deep dive
    personalities = {
        "Jia": {
            "strengths": "Natural leader who thrives on challenge. You see the big picture before others do and have an almost instinctive ability to chart direction. People naturally look to you when things are uncertain.",
            "relationships": "You attract people who need guidance and vision, but can overwhelm those who prefer a slower pace. Your ideal partner is someone who grounds your expansive energy — without clipping your branches.",
            "career": "Entrepreneurship, strategy, education, politics. You're built to lead, not follow. Your challenge is finding structures that don't constrain your growth instinct.",
            "daily": "Start your day with physical movement — Wood energy needs to circulate. Avoid overcommitting to too many projects; pick one and see it through before starting the next."
        },
        "Yi": {
            "strengths": "Gracefully persistent. You find elegant paths around obstacles that stop others cold. Your adaptability is your superpower — but don't mistake flexibility for weakness.",
            "relationships": "You connect deeply through empathy and understanding, but may struggle to articulate your own needs. Learn to ask for what you want directly — your partner cannot read your subtle signals.",
            "career": "Diplomacy, counseling, design, writing. Your strength is finesse, not force. Environments that reward nuance and patience will let you thrive.",
            "daily": "Practice direct communication — even when it's uncomfortable. Your tendency to adapt can blur your boundaries. Journal your true feelings before negotiating with others."
        },
        "Bing": {
            "strengths": "Your warmth is magnetic and genuine. You light up spaces without trying, and your enthusiasm is infectious. People remember how you made them feel.",
            "relationships": "You give generously — attention, energy, love. But Fire burns through fuel quickly. You need partners who replenish you, not just receive from you. Watch for one-sided dynamics.",
            "career": "Performance, coaching, sales, media. Wherever human connection matters, you excel. The danger: burning out in roles that demand constant emotional output without recovery time.",
            "daily": "Schedule deliberate rest between social engagements. You need solitude to recharge, even though you crave connection. Protect your mornings for yourself."
        },
        "Ding": {
            "strengths": "Your power is quiet but undeniable. You illuminate intimate spaces rather than stadiums, and those who know you are deeply loyal. You see things others miss.",
            "relationships": "You attract people who need warmth and understanding. Your challenge: making sure you're not always the giver. Let yourself be seen — your vulnerability is your strength.",
            "career": "Counseling, research, art, healing professions. Your gift is depth over breadth. Find the niche where your particular light is valued, not just any space that needs illumination.",
            "daily": "Trust your gentle nature. You don't need to be louder or brighter to matter. Create a sanctuary at home where your flame can burn steady and undisturbed."
        },
        "Wu": {
            "strengths": "You are the mountain others lean on — steady, reliable, immovable when it counts. Your presence alone creates stability in chaotic environments.",
            "relationships": "You attract those seeking security and grounding. But mountains can become isolated. Let people climb you — share your inner world, not just your strength.",
            "career": "Operations, finance, healthcare, construction. You build things that last. Avoid roles with constant disruption — your energy thrives on stability and incremental progress.",
            "daily": "Build routines that honor your natural rhythm. You don't need to be flexible like Water or dynamic like Fire — your gift is consistency. Protect it."
        },
        "Ji": {
            "strengths": "The fertile ground where others' dreams grow. You nurture, support, and resource with generosity that seems bottomless. People bloom in your presence.",
            "relationships": "You give endlessly, sometimes to your own depletion. Your growth edge: receiving. Let someone else be the ground for a while. You deserve nurturing too.",
            "career": "Teaching, healthcare, community organizing, hospitality. Your gift is creating conditions for growth. Find roles where your nurturing is valued as a professional skill.",
            "daily": "Ask yourself each morning: 'What do I need today?' before asking what others need. Self-care isn't selfish for Earth types — it's essential maintenance."
        },
        "Geng": {
            "strengths": "Your clarity cuts through confusion. You have a natural instinct for justice and an ability to see what's true when others are lost in emotion. Your decisiveness is a gift.",
            "relationships": "You value honesty above comfort, which can feel harsh to more sensitive types. Soften your delivery without diluting your truth. The sword that cuts clean doesn't need to wound.",
            "career": "Law, engineering, editing, critique. Your precision is your professional edge. Avoid environments that reward ambiguity — they'll frustrate your need for clarity.",
            "daily": "Practice delivering one kind truth per day. Your instinct is to state facts plainly — add warmth consciously. The message lands better when the messenger is gentle."
        },
        "Xin": {
            "strengths": "Your eye for quality and authenticity is extraordinary. You discern what truly matters from what's merely shiny. Your standards elevate everything you touch.",
            "relationships": "You seek depth and authenticity, but your high standards can create distance. Not everyone reaches your bar immediately — give people room to grow toward you.",
            "career": "Art, curation, design, quality control. Your gift is refinement. Roles that let you polish, select, and elevate will satisfy your need for excellence.",
            "daily": "Perfection is a direction, not a destination. Let one thing be 'good enough' each day. Your inner critic is useful — but don't let it become your inner tyrant."
        },
        "Ren": {
            "strengths": "You carry depths most people never see. Visionary, expansive, wise beyond your years. You think in systems and patterns that others need explained.",
            "relationships": "You attract those drawn to mystery and depth, but can feel unknowable even to those closest to you. Share your waters intentionally — let trusted people sail them.",
            "career": "Strategy, research, philosophy, creative direction. Your gift is seeing what others miss. Avoid surface-level roles — they'll bore you to exhaustion.",
            "daily": "Surface for air regularly. Your depth is a gift, but isolation is a risk. One meaningful conversation per day keeps Water types connected to the world."
        },
        "Gui": {
            "strengths": "Your intuition runs deep and true. You sense things before they happen, understand people without words, and carry a wisdom that seems ancient. Trust it.",
            "relationships": "You absorb others' emotions like mist absorbs scent — often without realizing it. Learn to distinguish your feelings from those you've picked up from others.",
            "career": "Psychology, art, spiritual guidance, research. Your gift is the invisible realm. Honor it by finding work that values intuition as much as logic.",
            "daily": "Ground yourself daily. Water types without Earth support get lost in the depths. Walk barefoot, cook a meal, do something physical that reminds you you're in a body."
        }
    }

    pers = personalities.get(dm, personalities["Wu"])

    # Element advice
    element_advice = {
        "Wood": "Harness your Wood energy for growth and expansion. Plant seeds for the future — your best work compounds over time. Avoid spreading too thin across too many projects.",
        "Fire": "Channel your Fire energy with intention. You burn bright — choose where to shine. Schedule rest between intensity; even the sun sets every day.",
        "Earth": "Ground your Earth energy in self-care. You support everyone else — make sure your own foundation is solid. The mountain that crumbles helps no one.",
        "Metal": "Sharpen your Metal energy with purpose. Your precision is a tool, not a weapon. Use it to build, not to cut down. Precision + compassion = wisdom.",
        "Water": "Direct your Water energy with clarity. Your depth is infinite — but depth without direction becomes a whirlpool. Set a course, then dive deep."
    }

    return {
        "name": name,
        "day_master": dm,
        "day_master_pinyin": dm,
        "day_master_wuxing": wuxing,
        "day_master_yinyang": yinyang,
        "archetype": dm_name,
        "dominant": dominant,
        "weakest": weakest,
        "balance": result['balance'],
        "balance_detail": result['balance_detail'],
        "growth_edge": growth,
        "pillars": pillars,
        "personality": pers,
        "element_advice": element_advice.get(wuxing, element_advice["Earth"]),
        "elements": result['elements'],
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        try:
            name = params.get('name', ['Friend'])[0]
            year = int(params.get('year', [2000])[0])
            month = int(params.get('month', [1])[0])
            day = int(params.get('day', [1])[0])
            hour = int(params.get('hour', [12])[0])
        except (ValueError, IndexError):
            self._respond(400, {"error": "Invalid parameters"})
            return

        try:
            report = build_report(name, year, month, day, hour)
            self._respond(200, report)
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)
