# Destiny Code — MVP Product Brief

## 1. Product Identity

**Product Name:** Destiny Code
**Tagline (One-Liner):** Your Personal Energy Blueprint — decoded from the ancient wisdom of BaZi, delivered for the modern seeker.
**Brand Voice:** Warm, insightful, empowering. Never mystical-hype, never fear-based.

## 2. Product Positioning

Destiny Code translates the 2000-year-old Chinese metaphysical system of BaZi (八字 / Four Pillars of Destiny) into a "Personal Energy Blueprint" — a self-discovery tool for the spiritually curious Western audience. We explicitly frame it as a personality and life-pattern analysis tool, not fortune-telling.

**Core Metaphor:** Just as your DNA encodes your physical traits, your birth moment encodes your energetic blueprint. We help you read it.

**Visual Identity:** Cyber Fengshui — dark zen aesthetic with neon accents, balancing ancient wisdom with digital-native design.

## 3. Target User Personas

### Persona A: "The Spiritual Explorer" (Core)
- Age: 28-42, urban professional
- Already uses Co-Star, pulls tarot, attends sound baths
- Seeks the "next level" beyond sun-sign astrology
- Willing to pay for depth and personalization
- Key phrase: "I feel like there's more to me than what Western astrology shows"

### Persona B: "The Self-Optimizer"
- Age: 25-38, tech/startup/freelance
- Uses Oura ring, journaling apps, personality tests (MBTI, Enneagram, Human Design)
- Treats spirituality as a performance-enhancement layer
- Wants actionable insight, not vague platitudes
- Key phrase: "How can understanding my energy patterns help me perform better?"

### Persona C: "The Crossroads Seeker"
- Age: 30-50, life transition (career change, divorce, existential crisis)
- New to Eastern systems but open-minded
- Looking for a framework to make sense of life patterns
- Willing to invest in clarity and direction
- Key phrase: "I keep repeating the same patterns and I don't know why"

## 4. MVP Scope

### IN SCOPE (Sprint 1)
- BaZi natal chart (本命盘 / Ben Ming Pan) interpretation only
- Four Pillars analysis: Year, Month, Day, Hour
- Day Master analysis
- Ten Gods (十神) distribution and meaning
- Five Elements balance assessment
- Personality, relational patterns, career inclinations
- One "life lesson" / growth edge
- Free preview (teaser) + paid full report

### OUT OF SCOPE (V2+)
- Annual luck cycles (大运 / Da Yun / 10-year luck pillars)
- Annual forecast (流年 / Liu Nian)
- Relationship compatibility / synastry (合盘)
- Date selection (择日)
- Live consultation / 1:1 reading
- Feng Shui integration
- Zi Wei Dou Shu (紫微斗数)

## 5. User Flow

```
Visitor lands on landing page
        ↓
Fills form: Name, Birth Date (YYYY-MM-DD), Birth Time, Birthplace
        ↓
System calculates BaZi chart (manual or CLI tool)
        ↓
Free preview generated & emailed instantly
  (≈150 words: Day Master + one key insight + CTA)
        ↓
User reads preview → CTA: "Unlock Your Full Energy Blueprint"
        ↓
Two paid tiers:
  - Complete Report ($29): 800-1200 word full interpretation
  - Deep Dive ($79): Add career path analysis + element balancing guide
        ↓
Report generated via AI (System Prompt V1) + human QA
        ↓
Manual delivery via email (first 50 reports)
```

## 6. Pricing Strategy

| Tier | Price | Content | Delivery |
|------|-------|---------|----------|
| Free Preview | $0 | Day Master identity, one key insight, element confirmation | Instant automated |
| Complete Report | $29 | Full 800-1200 word BaZi interpretation: energy overview, personality, relationships, career, growth edge | Manual (24-48h during MVP) |
| Deep Dive | $79 | Everything in Complete + career path deep-dive + element balancing action guide + 1 follow-up question via email | Manual (48-72h during MVP) |

**Pricing Rationale:**
- Below Co-Star premium ($39.99/yr) on per-unit basis, but higher one-time — justified by depth
- Comparable to a 30-min astrology consultation ($50-100)
- $29 is an impulse-buy price point for the target demographic
- High-trust manual delivery in MVP justifies premium positioning later

## 7. Competitive Landscape & Differentiation

| Competitor | What They Do | Our Differentiation |
|------------|-------------|---------------------|
| **Co-Star** | AI Western astrology, daily push notifications, social | We offer a completely different system (BaZi is element-based, not planet-based). More depth per reading. Not an app — a premium report. |
| **The Pattern** | Astrology-based personality analysis, "bond" features | They use Western astrology. No BaZi player in English at this UX quality level. Our go-to-market is "the astrology alternative." |
| **Sanctuary** | Live astrologer chat + daily horoscopes | Marketplace model vs. our expert-report model. We own the interpretive layer; they broker access to humans. |
| **AstroTalk** | Indian astrology marketplace (primarily Vedic) | India-centric, Vedic focus. We target Western seekers with a distinctly East Asian system — novelty + authenticity. |
| **Human Design apps** | Bodygraph-based personality system | Different system altogether. But our "Energy Blueprint" framing competes in the same mental shelf-space. |

**Key Differentiation Points:**
1. **System novelty:** BaZi is virtually unknown in the West — first-mover advantage for premium positioning
2. **Element-based:** Five Elements (Wood, Fire, Earth, Metal, Water) are intuitive and resonate with wellness/wellbeing trends
3. **Not an app:** Premium, human-touched report vs. automated push notifications — higher perceived value
4. **Anti-fear positioning:** All competitors have "bad transit" messaging; we explicitly reject fear-based engagement
5. **"Energy Blueprint" framing:** Aligns with Human Design / Gene Keys aesthetic without copying them

## 8. Success Metrics (MVP)

- Landing page conversion to free preview: > 15%
- Free preview → paid conversion: > 8%
- Report satisfaction rating: > 4.5/5
- Refund rate: < 5%
- Referral rate: > 10% (measured via "how did you hear about us")

## 9. Timeline (Sprint 1)

- Week 1: Landing page live, free preview flow working
- Week 2: System Prompt V1 finalized, first 10 manual reports delivered
- Week 3: Iterate prompt based on feedback, refine templates
- Week 4: 50 reports delivered, decide go/no-go for automation

---

*Document Version: 1.0 | Sprint: 1 | Last Updated: 2026-05-30*
