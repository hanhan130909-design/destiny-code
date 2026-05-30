# Free Preview Report Template — Destiny Code

> This template is used for the free preview email sent immediately after a user submits their birth details. It reveals approximately 20% of the full report, designed to create enough value to build trust while leaving a strong curiosity gap that drives paid conversion.

---

## When to use this template

- User has submitted the birth form on the landing page
- BaZi chart has been calculated (manually or via CLI tool at this MVP stage)
- You have identified: Day Master element, Five Elements count, and 1-2 prominent Ten Gods
- Send within 5 minutes of form submission (automated trigger, manually executed in MVP)

---

## Template

```
Subject: {Name}, your Energy Blueprint is ready ✨

---

Hi {Name},

Thank you for trusting Destiny Code with your birth information. Your Personal Energy Blueprint has been calculated using the ancient BaZi system — a 2,000-year-old framework that maps the energetic signature of your birth moment.

Here's a first glimpse into your cosmic design:

---

🌿 YOUR ELEMENTAL SIGNATURE

You are a **{DayMasterElement} {DayMasterPolarity}** Day Master — specifically the **{DayMasterStem}** energy.

{DayMasterOneLiner}

This means: {DayMasterPersonalitySentence}

---

🔥 YOUR ELEMENTAL LANDSCAPE

Your chart's elemental balance shows:

{ElementBreakdownBullets}

Your most prominent energy: **{MostAbundantElement}** — {MostAbundantElementInsight}
Your growth catalyst: **{LeastAbundantElement}** — this is an energy that invites you to stretch and evolve.

---

🌀 YOUR LIFE'S CURRICULUM — A FIRST GLIMPSE

Based on the configuration of your chart, one of the key growth themes woven into your blueprint is:

**{LifeThemeTitle}**

{LifeThemeParagraph — 2-3 sentences, warm, intriguing, leaves a question in the reader's mind}

---

🔮 READY TO GO DEEPER?

Your free preview has revealed about 20% of what your Energy Blueprint contains. The **Complete Destiny Code Report** includes:

✨ Your full Personality Architecture — how your Ten Gods shape who you are
🌊 The elemental dynamics that drive your decisions, relationships, and energy
💫 Your Relationship Mirror — what you seek, attract, and are here to learn in partnership
🎯 Your Vocational Compass — the career directions your blueprint naturally supports
🌀 All your Life Curricula — the full map of growth themes in your chart
📖 Practical integration guidance — how to work with your energy, not against it

---

**Unlock Your Full Energy Blueprint → $29**
[CTA Button: GET MY COMPLETE REPORT]

Prefer the deepest dive? The **Deep Dive Report ($79)** adds a career path analysis and a personalized Element Balancing Guide with actionable practices.

[Secondary CTA: EXPLORE DEEP DIVE]

---

With warmth,

The Destiny Code Team ⛩️

*Your Energy Blueprint is a mirror, not a cage. The ancient sages said: know your chart, then transcend it.*
```

---

## Template Variable Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `{Name}` | User's first name | Alex |
| `{DayMasterElement}` | The Five Element of the Day Master | Earth |
| `{DayMasterPolarity}` | Yin or Yang | Yang |
| `{DayMasterStem}` | The Heavenly Stem character + pinyin | 戊 (Wu) |
| `{DayMasterOneLiner}` | 1-sentence archetype of this Day Master | "the energy of the mountain" |
| `{DayMasterPersonalitySentence}` | 1-2 sentences on personality | "You carry a natural stability and reliability that others instinctively lean on..." |
| `{ElementBreakdownBullets}` | Bullet list of element counts | 🪵 Wood: 2 · 🔥 Fire: 1 · 🌍 Earth: 3 · ⚙️ Metal: 1 · 💧 Water: 2 |
| `{MostAbundantElement}` | Element with highest count | Earth |
| `{MostAbundantElementInsight}` | Brief insight about the abundant element | "You're deeply grounded, practical, and naturally create stability around you." |
| `{LeastAbundantElement}` | Element with lowest count | Metal |
| `{LifeThemeTitle}` | Short phrase capturing a key life theme | "Learning the Power of Discernment" |
| `{LifeThemeParagraph}` | 2-3 warm, intriguing sentences about this theme. End with a question that makes them want to read more. | "Your chart suggests that one of your soul's primary invitations is to develop the art of saying 'no.' With abundant creative energy, your natural instinct is to say 'yes' to every possibility — but your blueprint reveals that your deepest fulfillment comes when you channel your gifts into fewer, deeper commitments. What might change if you allowed yourself to focus on just one thing for the next six months?" |

---

## Fill-in Guide: Day Master One-Liners

Use this quick reference when writing the `{DayMasterOneLiner}` field:

| Day Master Stem | One-Liner |
|-----------------|-----------|
| 甲 (Jia) — Yang Wood | "the towering tree — pioneer spirit and natural leadership" |
| 乙 (Yi) — Yin Wood | "the resilient vine — graceful, adaptable, and quietly unstoppable" |
| 丙 (Bing) — Yang Fire | "the sun itself — radiant, generous, and impossible to ignore" |
| 丁 (Ding) — Yin Fire | "the candle flame — warm, magnetic, with a light that draws others in" |
| 戊 (Wu) — Yang Earth | "the mountain — steady, protective, and immovable when it matters" |
| 己 (Ji) — Yin Earth | "the fertile soil — nurturing, resourceful, the ground where things grow" |
| 庚 (Geng) — Yang Metal | "the sword — decisive, principled, with a natural instinct for justice" |
| 辛 (Xin) — Yin Metal | "the jewel — refined, discerning, with an eye for what truly matters" |
| 壬 (Ren) — Yang Water | "the ocean — visionary, expansive, carrying depths most never see" |
| 癸 (Gui) — Yin Water | "the mist — subtle, intuitive, a quiet wisdom that permeates everything" |

---

## Life Theme Ideas (for inspiration)

Mix and match based on the actual chart. Always frame as an invitation, never a flaw.

| Chart Feature | Sample Life Theme |
|---------------|-------------------|
| Strong Output (Eating God / Hurting Officer) | "From Creative Flow to Creative Focus" |
| Weak Officer (Direct Officer / Seven Killings) | "Building Your Inner Compass" |
| Strong Resource (Direct / Indirect Resource) | "From Knowing to Doing — Bridging Wisdom and Action" |
| Strong Wealth (Direct / Indirect Wealth) | "The Art of Receiving — Allowing Abundance Without Chasing" |
| Many Friends (Bi Jian / Jie Cai) | "Self-Reliance and the Power of Letting Others In" |
| Day Master out of season | "Finding Your Ground — Thriving Beyond Your Comfort Zone" |
| Seven Killings present | "Channeling Your Intensity — From Pressure to Power" |
| Balanced chart | "The Dance of Balance — Honoring All Parts of Your Design" |

---

## Quality Checklist Before Sending

- [ ] All `{variables}` have been replaced with actual values
- [ ] The Day Master insight is accurate and feels personal
- [ ] The Life Theme is intriguing but not alarming — leaves a positive curiosity gap
- [ ] Element counts are correct
- [ ] CTA links work
- [ ] No fear-based language
- [ ] No promises of specific future events
- [ ] Tone is warm and empowering
- [ ] Email renders correctly (test in Gmail + mobile)

---

## Notes for MVP Operations

- **During MVP (first 50 reports):** The BaZi chart is calculated manually or via a CLI tool. Someone on the team fills in this template manually and sends the email.
- **Automation target (post-MVP):** Hook up a BaZi calculation API → auto-fill template → auto-send via email service (e.g., Resend, SendGrid).
- **Conversion tracking:** Each CTA link should include a UTM parameter (e.g., `?utm_source=free_preview&utm_medium=email`) to measure conversion rate.

---

*Template Version: 1.0 | Sprint: 1 | Last Updated: 2026-05-30*
