# Free Preview Report Template V2 — Destiny Code

> Sent instantly after user submits birth details. ~300–400 words.
> Structure: Element Briefing → Day Master Personality → Current Energy Theme → CTA Hook.
> Must feel like genuine value, not a scam. The curiosity gap is real — the full report genuinely contains the rest.
> Version: 2.0 | Sprint: 2 | Last Updated: 2026-05-31

---

## THE TEMPLATE (Copy-ready for email / landing page inline)

```
Subject: {Name}, your Energy Blueprint has been decoded ✨

---

Hi {Name},

Your birth moment carries a unique energetic signature — and we've decoded it using BaZi, the 2,000-year-old Chinese system of elemental wisdom. Here is your first glimpse.

---

🌿 YOUR ELEMENTAL BRIEFING

Your chart's five-element balance reveals your natural energetic landscape:

{WoodIcon} Wood ({WoodCount}): {WoodInsight}
{FireIcon} Fire ({FireCount}): {FireInsight}
{EarthIcon} Earth ({EarthCount}): {EarthInsight}
{MetalIcon} Metal ({MetalCount}): {MetalInsight}
{WaterIcon} Water ({WaterCount}): {WaterInsight}

Your most abundant energy is **{MostAbundantElement}** — {MostAbundantInsight}. Your most catalytic energy — the one inviting your deepest growth — is **{LeastAbundantElement}**. {LeastAbundantInsight}.

---

🌀 YOUR CORE SELF

You are a **{DayMasterElement} {DayMasterPolarity}** Day Master — specifically the **{DayMasterStem}** energy, known as {DayMasterArchetype}.

{DayMasterPersonality}

---

⚡ YOUR CURRENT ENERGY THEME

Based on the architecture of your chart, a theme that runs through your design is:

**{EnergyThemeTitle}**

{EnergyThemeDescription}

{CuriosityQuestion}

---

🔮 YOUR FULL BLUEPRINT AWAITS

This preview has shown you roughly 15% of what your Energy Blueprint contains. The **Complete Destiny Code Report** ($29) reveals the full picture:

✦ Your complete Personality Architecture — how all your Ten Gods weave together
✦ Your Relationship Mirror — partnership patterns, what you seek and attract
✦ Your Vocational Compass — the career paths your blueprint naturally supports
✦ Your Life's Curriculum — every growth theme woven into your design
✦ Practical integration guidance — how to work with your energy, not against it

→ [Unlock Your Complete Report — $29]

Prefer the deepest dive? The **Deep Dive Report** ($79) adds a personalized Career Path Analysis and an Element Balancing Guide with daily practices.

→ [Explore the Deep Dive]

---

With warmth,
The Destiny Code Team ⛩️

*Your Blueprint is a mirror, not a cage. Know your chart, then transcend it.*
```

---

## VARIABLE FILL-IN GUIDE

### Opening & Closing
| Variable | Source | Example |
|----------|--------|---------|
| `{Name}` | Form input — use first name only | Sarah |

### Element Briefing
| Variable | Source | Example |
|----------|--------|---------|
| `{WoodIcon}` / `{FireIcon}` / etc. | Emoji per element | 🪵 / 🔥 / 🌍 / ⚙️ / 💧 |
| `{WoodCount}` / etc. | `fiveElementsBalance.Wood` etc. from chart JSON | 3 |
| `{WoodInsight}` | 5-8 words on what this count means. See Fill-in Phrases below. | "Your vision and growth drive are naturally abundant" |
| `{MostAbundantElement}` | Element with highest count | Fire |
| `{MostAbundantInsight}` | 1 sentence: what this abundance means as a gift | "You radiate warmth and passion naturally — people feel energized around you." |
| `{LeastAbundantElement}` | Element with lowest count (non-zero if possible) | Metal |
| `{LeastAbundantInsight}` | 1 sentence: growth invitation, never "you lack" | "This energy invites you to develop discernment — the art of choosing what truly matters." |

### Day Master
| Variable | Source | Example |
|----------|--------|---------|
| `{DayMasterElement}` | `dayMaster.element` from chart JSON | Earth |
| `{DayMasterPolarity}` | `dayMaster.polarity` from chart JSON | Yang |
| `{DayMasterStem}` | `dayMaster.stem` from chart JSON | 戊 (Wu) |
| `{DayMasterArchetype}` | From archetype table below | "the mountain — steady, protective, and immovable when it matters" |
| `{DayMasterPersonality}` | 2 sentences. From Day Master Reference in System Prompt V2. Always include one gift + one growth edge. | "You are someone others instinctively lean on. Your growth edge lies in learning to bend — the mountain that never shifts can become isolated." |

### Energy Theme
| Variable | Source | Example |
|----------|--------|---------|
| `{EnergyThemeTitle}` | Short evocative phrase derived from dominant Ten God or element pattern | "Channeling Your Creative Fire" |
| `{EnergyThemeDescription}` | 2-3 sentences. Warm, genuine, specific to their chart. Never vague platitudes. | "Your chart shows an abundance of Creative Flow energy — you're someone who generates ideas and beauty almost effortlessly. The invitation woven into your blueprint is learning to pair that creative fire with structure, so your gifts build something lasting rather than burning bright and fading." |
| `{CuriosityQuestion}` | 1 sentence. A genuine, open question that makes them want to know more. Not clickbait. | "What might shift if you gave your most important creative project six months of undivided attention?" |

---

## FILL-IN PHRASES BY ELEMENT COUNT

Use these to quickly write the `{ElementInsight}` fields. Pick the phrase matching the count.

### Wood (🪵)
| Count | Insight Phrase |
|-------|---------------|
| 0 | "Vision and new beginnings are an invitation your chart asks you to consciously cultivate" |
| 1 | "A quiet but persistent capacity for growth and fresh starts" |
| 2 | "A natural balance of vision — you see possibilities without being overwhelmed by them" |
| 3 | "Abundant growth energy — you're a natural initiator with a vision-driven mind" |
| 4+ | "A powerful pioneering force — new ideas and expansion are your native language" |

### Fire (🔥)
| Count | Insight Phrase |
|-------|---------------|
| 0 | "Self-expression and passion are an invitation — your chart asks you to kindle your inner spark" |
| 1 | "A precious inner flame — when you express yourself, it matters" |
| 2 | "Warm and naturally expressive — people feel seen and energized around you" |
| 3 | "Radiant presence — you bring warmth, enthusiasm, and charisma to every room" |
| 4+ | "A blazing sun — your passion is magnetic and your self-expression is a force" |

### Earth (🌍)
| Count | Insight Phrase |
|-------|---------------|
| 0 | "Stability and grounding are a conscious practice — your growth edge is building inner steadiness" |
| 1 | "A quiet anchor within — you find your footing even in uncertainty" |
| 2 | "Naturally grounded — you create stability that others rely on" |
| 3 | "Deeply stable and nurturing — you're the foundation people build their lives around" |
| 4+ | "Mountain-strong — your steadiness and practicality are your superpower" |

### Metal (⚙️)
| Count | Insight Phrase |
|-------|---------------|
| 0 | "Discernment and boundaries are an invitation — choosing what to let go of is a key growth area" |
| 1 | "A quiet inner compass of quality — you know what's worth your energy" |
| 2 | "Clear-eyed and discerning — you naturally distinguish what matters from what doesn't" |
| 3 | "Sharp perception and strong principles — you bring structure and clarity wherever you go" |
| 4+ | "A natural architect of systems and boundaries — your precision and standards are exceptional" |

### Water (💧)
| Count | Insight Phrase |
|-------|---------------|
| 0 | "Inner flow and intuition are an invitation — stillness may be your gateway to deeper wisdom" |
| 1 | "A quiet well of intuition — you know things without knowing how you know them" |
| 2 | "Deeply perceptive and adaptable — you read people and situations with ease" |
| 3 | "Oceanic depth — your intuition, emotional intelligence, and wisdom run deep" |
| 4+ | "A vast inner world — your depth of perception and intuitive wisdom are profound" |

---

## DAY MASTER ARCHETYPE QUICK REFERENCE (for `{DayMasterArchetype}`)

| Stem | Archetype |
|------|-----------|
| 甲 (Jia) | "the towering tree — pioneer spirit and natural leadership" |
| 乙 (Yi) | "the resilient vine — graceful, adaptable, and quietly unstoppable" |
| 丙 (Bing) | "the sun itself — radiant, generous, and impossible to ignore" |
| 丁 (Ding) | "the candle flame — warm, magnetic, with a light that draws others close" |
| 戊 (Wu) | "the mountain — steady, protective, and immovable when it matters" |
| 己 (Ji) | "the fertile soil — nurturing, resourceful, the ground where things grow" |
| 庚 (Geng) | "the sword — decisive, principled, with a natural instinct for justice" |
| 辛 (Xin) | "the jewel — refined, discerning, with an eye for what truly matters" |
| 壬 (Ren) | "the ocean — visionary, expansive, carrying depths most never see" |
| 癸 (Gui) | "the mist — subtle, intuitive, a quiet wisdom that permeates everything" |

---

## ENERGY THEME QUICK REFERENCE (for `{EnergyThemeTitle}`)

Choose based on the most prominent chart feature:

| Chart Feature | Energy Theme Title |
|---------------|-------------------|
| Strong Eating God (Creative Flow) | "From Creative Spark to Creative Legacy" |
| Strong Hurting Officer (Trailblazer) | "Channeling Your Boundary-Breaking Brilliance" |
| Strong Direct/Indirect Resource (Wisdom) | "From Inner Knowing to Outer Expression" |
| Strong Direct/Indirect Wealth (Resources) | "The Art of Receiving — Allowing Abundance Without Chasing" |
| Strong Direct Officer (Inner Compass) | "Leading with Integrity — Your Natural Authority" |
| Seven Killings present (Intensity) | "Channeling Your Intensity — From Pressure to Power" |
| Many Friend/Rob Wealth (Self-Reliance) | "Self-Reliance and the Power of Letting Others In" |
| Day Master out of season | "Finding Your Ground — Thriving Beyond Your Comfort Zone" |
| Balanced chart | "The Dance of Balance — Honoring All Parts of Your Design" |

---

## QUALITY CHECKLIST (Before sending)

- [ ] All `{variables}` replaced with actual, accurate values
- [ ] Element counts match the chart's `fiveElementsBalance`
- [ ] Day Master archetype is correct for their stem + polarity
- [ ] Energy theme is specific to their chart, not generic
- [ ] Curiosity question is genuine and open-ended, not manipulative
- [ ] Total word count is 300–400 words (the template body, not including subject line)
- [ ] No fear-based language anywhere
- [ ] No promises of specific future outcomes
- [ ] CTA links are functional and UTM-tagged
- [ ] Tone is warm, personal, and confident — not salesy

---

## EXAMPLE FILLED PREVIEW

```
Subject: Maya, your Energy Blueprint has been decoded ✨

---

Hi Maya,

Your birth moment carries a unique energetic signature — and we've decoded it using BaZi, the 2,000-year-old Chinese system of elemental wisdom. Here is your first glimpse.

---

🌿 YOUR ELEMENTAL BRIEFING

Your chart's five-element balance reveals your natural energetic landscape:

🪵 Wood (2): A natural balance of vision — you see possibilities without being overwhelmed by them
🔥 Fire (3): Radiant presence — you bring warmth, enthusiasm, and charisma to every room
🌍 Earth (1): A quiet anchor within — you find your footing even in uncertainty
⚙️ Metal (1): A quiet inner compass of quality — you know what's worth your energy
💧 Water (1): A quiet well of intuition — you know things without knowing how you know them

Your most abundant energy is **Fire** — you radiate warmth and enthusiasm naturally, and people instinctively feel more alive around you. Your most catalytic energy — the one inviting your deepest growth — is **Earth**. This invites you to build more grounded structures around your brilliant fire, so your passion creates things that last.

---

🌀 YOUR CORE SELF

You are a **Fire Yang** Day Master — specifically the **丙 (Bing)** energy, known as the sun itself — radiant, generous, and impossible to ignore.

You are someone who lights up a room without trying. Your natural warmth draws people in, and your enthusiasm is genuinely infectious. Your growth edge lies in learning to sustain your fire without burning out — the sun doesn't need to shine at full intensity in every moment to be powerful.

---

⚡ YOUR CURRENT ENERGY THEME

Based on the architecture of your chart, a theme that runs through your design is:

**From Creative Spark to Creative Legacy**

Your chart reveals an abundance of Creative Flow energy — you generate ideas, beauty, and inspiration almost effortlessly. The invitation woven into your blueprint is learning to pair that creative fire with discernment and structure. You're not here just to spark; you're here to build something that outlasts you.

What might shift if you chose one creative project and gave it your undistracted attention for the next six months?

---

🔮 YOUR FULL BLUEPRINT AWAITS

This preview has shown you roughly 15% of what your Energy Blueprint contains. The **Complete Destiny Code Report** ($29) reveals the full picture — your full Personality Architecture, Relationship Mirror, Vocational Compass, all your Life Curricula, and practical integration guidance.

→ [Unlock Your Complete Report — $29]

---

With warmth,
The Destiny Code Team ⛩️

*Your Blueprint is a mirror, not a cage. Know your chart, then transcend it.*
```

Word count of example: 357 words ✓

---

*Template Version: 2.0 | Sprint: 2 | Last Updated: 2026-05-31*
