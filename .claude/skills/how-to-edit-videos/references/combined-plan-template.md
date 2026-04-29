# Combined plan — table format and assignment rules

The combined plan is the document Marlon approves **before** any kie.ai call OR any HTML write. It covers BOTH cutaway images and motion graphics in one table — so he reviews the whole video timeline as a single document and edits anything before generation.

Always present it as a markdown table in chat — never write to disk and ask "look at this file".

## Table format (use these columns every time, sorted by `start`)

```
| id | start | dur | kind | trigger word | type | copy / description | style |
|----|-------|-----|------|--------------|------|--------------------|-------|
```

| Column | What goes in it |
|---|---|
| `id` | Short kebab-case slug. For cutaways it becomes the PNG filename (`rank-map`, `revenue-graph`). For MGs it's a stable handle (`mg-stamp-by-design`, `mg-cta`). |
| `start` | Seconds. The moment the beat lands on screen — usually the start time of the trigger word from the transcript. |
| `dur` | Seconds. **Cutaway: 0.8–2.0s typical, ≤3s hard** (vertical short-form b-roll norm — keeps cadence tight). **MG:** stamps 1.5–3s, lists 3–5s, CTA 5–7s. |
| `kind` | `cutaway` or `mg`. The assignment rule decides this — see below. |
| `trigger word` | The exact word in the transcript the beat appears on. Quote it. |
| `type` | For cutaways: `stat-card`, `graph`, `rank-map`, `infographic`, `before-after`, `comparison`, `screenshot`. For MGs: `stamp`, `list`, `chip`, `cta`. |
| `copy / description` | **Cutaways:** one sentence describing the image + the on-image text quoted exactly. **MGs:** the full on-screen layout — eyebrow line, headline, sub, footer, with palette tone (pain / solution / CTA). |
| `style` | Visual style hint. Cutaway default: `flat infographic, dark navy bg #0A0F1F, single accent color, large legible type, no photoreal humans`. MG default: existing palette per audience. |

## The assignment rule (decides `kind` for every beat)

| Beat is about... | `kind` | Why |
|---|---|---|
| A concrete thing the speaker names (map, real chart, screenshot, photo, place) | `cutaway` | Image *shows* the thing |
| An abstract claim, number, list, or stamp | `mg` | Kinetic typography wins for DR clarity; speaker face holds trust |
| The CTA at close | `mg` | Always — face must be visible during the conversion ask |
| The 25–35s pattern interrupt | `cutaway` (preferred) | Drop-off cliff — biggest possible visual change |

**No double-encoding.** If a cutaway shows "$50K", don't fire an MG stamp also saying "$50K". Pick one channel per claim.

**Rotation rhythm.** Walk the table top-to-bottom: never two `cutaway` rows back-to-back; never two `mg` rows back-to-back without a speaker beat (≥2.5s gap) between.

**Validation gates (BLOCKING — check before generation):**
1. **First-30s gate:** ≥3 visual beats with `start < 30`. If fewer, add front-loaded beats.
2. **Max-stretch gate:** for every adjacent beat pair where `prev.start ≥ 10`, `next.start − (prev.start + prev.dur) ≤ 8.0`. No speaker-only gap >8s after t=10s. Insert a 0.8–2.0s cutaway into any failing gap.
3. **Cadence gate:** `total_beats / (runtime_seconds / 60) ≥ 8`. Below 8 beats/min reads as static.
4. **Budget gate:** sum(`dur` where kind=mg) ≤ 25% of runtime; sum(`dur` where kind=cutaway) ≤ 15% of runtime; combined ≤ 35%.

## Worked example (90s ad)

```
| id              | start | dur | kind    | trigger word | type      | copy / description                                                                                                                                                                       | style                                              |
|-----------------|-------|-----|---------|--------------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| mg-niche        | 6.27  | 3.0 | mg      | "dental"     | stamp     | EYEBROW: "FOR" / HEADLINE: "DENTAL CLINIC OWNERS" / SUB: "in Australia" — solution palette (green #22D27C)                                                                                | Anton headline, dark plate                         |
| cut-rank-map    | 16.5  | 2.5 | cutaway | "rankings"   | rank-map  | Australian map with five city pins (Sydney, Melbourne, Brisbane, Perth, Adelaide). Yellow "#1" badge over Sydney pin. Headline reads "WHO RANKS #1". No photoreal humans.                 | flat infographic, dark navy bg, yellow accent      |
| cut-revenue     | 31.0  | 2.5 | cutaway | "doubled"    | graph     | Bar chart, 2 bars: BEFORE small in red #FF3B3B, AFTER tall in green #22D27C. Big stamp "+118%" above. No axis labels.                                                                     | flat, single screen, huge numerals, vertical 9:16  |  ← 25–35s interrupt = cutaway ✓
| mg-list         | 50.5  | 4.0 | mg      | "three"      | list      | EYEBROW: "EVERY CLINIC GETS WRONG" / HEADLINE: "3 THINGS" / ROWS: "1. NO LOCAL SEO   2. NO REVIEW SYSTEM   3. NO BLOG" — pain palette (red #FF3B3B)                                       | Anton, dark plate                                  |
| cut-inbox       | 64.8  | 2.2 | cutaway | "inbox"      | screenshot| Stylized phone notification stack on a dental clinic app: 12 new appointment notifications, each with a green check, time stamps "8:14 AM", "9:02 AM" etc. Headline "12 NEW PATIENTS".   | flat illustration, dark bg, green accent           |
| mg-cta          | 84.96 | 6.7 | mg      | "click"      | cta       | EYEBROW: "READY?" / HEADLINE: "BOOK A FREE CALL" / BULLETS: "Free 30-min strategy / No obligation / Australia-only" / FOOTER: "👇 Click below" — CTA palette (yellow #FFE500 at low alpha) | Anton headline, yellow bullets                     |
```

Total visual coverage: 21.0s / 90s = 23% — under the 35% cap ✓
First beat: 6.27s — past the 5s minimum ✓
25–35s interrupt: cut-revenue at 31.0s — cutaway ✓
Rotation: mg → cutaway → cutaway ❌ — wait, mg-niche → cut-rank-map → cut-revenue would be two cutaways. Check gaps: cut-rank-map ends at 19.0, cut-revenue starts at 31.0 → 12s gap, way past the 3s minimum, so this is fine (the rotation rule is about *adjacent without speaker between*, and 12s of speaker is plenty). Walk: mg → speaker → cutaway → speaker → cutaway → speaker → mg → speaker → cutaway → speaker → mg(CTA) ✓
CTA: kind=mg ✓

## Prompt rules for cutaways (gpt-image-2 specifics)

The model renders text *better* than most diffusion models but it's still imperfect. Rules that produce reliable output:

1. **Keep on-image text short.** ≤8 words on any single visual. Long sentences come out garbled.
2. **Quote the exact text.** In the prompt say `the headline reads "WHO RANKS #1"` — not `a headline about ranking`.
3. **Specify aspect explicitly in the prompt** as well as the API param: `vertical 9:16 composition` (or whatever the source aspect is). Belt-and-braces.
4. **High-contrast background or solid plate behind text.** Same logic as MG plates — text on busy backgrounds is unreliable.
5. **Single focal element.** A graph OR a stat OR a map — not all three. Stack reads as cluttered at video preview size.
6. **No photoreal humans.** They drift uncanny and steal trust from the speaker. Stick to icons, glyphs, charts, simplified illustrations.
7. **Exclude branding.** No logos, no real company names, no real product shots — those cause moderation flags and aren't ours to use.
8. **Vertical-safe composition.** "All key content in the vertical center column" — protects against any cropping if the model drifts off-ratio.

## MG copy rules (the on-screen text)

1. **Eyebrow** = the setup line (small caps above the headline). Optional — drop if it duplicates the headline.
2. **Headline** = the punch — one phrase, ≤4 words ideally, ≤7 words max. Anton uppercase.
3. **Sub** = optional context line below the headline. Smaller. Often one line of body text.
4. **Footer** = an optional trailing line that mirrors a phrase the speaker says at the end of the beat (animates in as a block, not word-by-word).
5. **Palette tone.** Pain = red, solution = green, CTA = yellow. Match the narrative weight.
6. **No copy that duplicates the captions verbatim.** Captions already render the speaker's words; the MG should add the *frame* (eyebrow context, headline distillation, list structure) — not echo.

## Drop priorities (when over budget)

When cutaways + MGs > 35% of runtime, drop in this order:
1. Redundant MG stamps that re-state what captions already cover (no double-encoding)
2. Decorative cutaways that don't visualize a specific concrete thing
3. Adjacent same-kind beats merge into one
4. **Never drop:** the 25–35s interrupt, the CTA, the opening niche reveal (if present)

## Iteration loop

Marlon reads the table → either edits a row inline (e.g. "change cut-rank-map description to include Brisbane and Sydney specifically", or "swap mg-list copy to 1. NO REVIEWS / 2. NO MAP / 3. NO PHOTOS") or says "go". Only "go" triggers generation.

After build:
- Cutaway re-do: edit the row's `description`, re-run the generator with `--force` for that id
- MG copy change: edit in chat or directly in `index.html` — no API call
- New beat: add a row, get re-approval, regenerate (idempotent), wire in
