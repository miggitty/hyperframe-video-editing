---
name: how-to-edit-videos
description: Edit Marlon's talking-head videos into polished short-form ads (Facebook / Instagram / Reels) using HyperFrames — Hormozi-style word-by-word captions, motion graphics that punctuate narrative pivots, AI-generated full-frame story images (graphs, rank maps, stat cards) via the kie.ai gpt-image-2 API, and a ghosted speaker behind full-frame graphics for continuity. Use this skill alongside the `hyperframes` skill whenever the user asks to edit, caption, subtitle, add motion graphics, or add image takeovers to a talking-head video, especially for paid social ads (Facebook ads, Instagram ads, Reels), explainer ads, lead-gen video ads, or any video aimed at healthcare practice owners (dentists, chiropractors, podiatrists, PTs). Trigger on phrases like "make a Facebook ad from this video", "add Hormozi-style subtitles", "edit this talking-head video", "add motion graphics to this", "add images to this video", "9:16 ad", "social ad video", or whenever the user provides a raw .mp4 of themselves talking and wants it turned into a finished ad. Use even when the user doesn't explicitly say "Hormozi" or "Facebook" — if the input is a talking-head video and the goal is a short-form ad, this skill applies.
---

# How to edit Marlon's videos

This skill captures the conventions Marlon validated through the `ad-marketing-truth` build. It runs alongside the `hyperframes` skill: hyperframes handles the framework mechanics (data attributes, GSAP, captions reference); this skill handles **the editorial style and the questions to ask before building**.

## Model recommendation: use Sonnet 4.6, not Opus

This skill is highly prescriptive — the beat budget, MG placement, palette, caption layout, and timing math are all spelled out. There's almost no open-ended reasoning required. **Sonnet 4.6 (`claude-sonnet-4-6`) is the right default** for running this skill: it's roughly 5× cheaper than Opus per token at no quality cost on this workflow. Reserve Opus 4.6/4.7 for rare cases where the user asks for an open-ended creative redesign, a new genre of ad outside the playbook, or debugging a genuinely unfamiliar edge case (e.g. a non-9:16 source).

The repo defaults to Sonnet via `.claude/settings.json` at the workspace root. If a session is on Opus, suggest `/model claude-sonnet-4-6` before doing the heavy work.

## Token-efficiency rules (cost-saving — important)

A typical edit session re-bills its full context on every turn, so big reads are expensive. Before doing them:

- **Don't `Read` `transcript.json` end-to-end.** It's ~1200 lines per minute of source. Use `python3 -c` to print just the word count, the first/last entries, or a slice. Or `jq` for filtered queries.
- **Don't `Read` `groups.json`.** It's a single huge JSON line. Inspect with `python3 -c "g=json.load(open('groups.json')); print(len(g), g[0], g[-1])"`.
- **Read `SKILL.md` once with `limit: 200`** and re-read targeted sections only when needed. The full file is ~600 lines.
- **Don't re-read files just to verify a write succeeded.** The `Write` / `Edit` tool result is authoritative.
- **Use the `Explore` sub-agent for codebase searches** that span more than a couple files — its intermediate context is discarded; only its summary returns.
- **Skip `Read` of generated images** — `ffprobe` for dimensions is enough.

## Hard rule: never edit, trim, or cut the source video or audio

**THE SOURCE IS IMMUTABLE INPUT.** It has already been edited by Marlon's video editor. Pauses, breaths, and "whitespace" are deliberate. This skill's job is to *add* captions and motion graphics on top — never to remove, trim, splice, fade, shorten, speed up, or alter any part of the source. Cutting any of it ruins the video.

What that means concretely:

- **Composition duration must fully cover the source.** Probe with `ffprobe`, then set `data-duration` on the root composition, the `<video>`, and the `<audio>` to the **source's full duration rounded up to the next 0.5s** (e.g. source 90.566s → `data-duration="91"`). Never set duration shorter than the source.
- **`<video>` runs from `data-start="0"` for the full source duration.** No `data-end`, no trims, no clip splicing.
- **`<audio>` runs from `data-start="0"` for the full source duration with `data-volume="1"`.** Never tween audio volume. Never insert silence. Never overlay music or VO. Never remove "dead air" or pauses.
- **Word-level captions follow the actual transcript end-time.** If whisper's transcript extends past the source's real audio (it sometimes hallucinates a trailing word), trim the *last caption group only* so its `e` ≤ the source's audio duration. Do not edit any earlier captions. Do not retime words.
- **Motion graphic windows are additive overlays on top of the video.** They never replace, mute, or skip a portion of the source — the speaker is always playing underneath at ghost opacity.
- **No transitions that shorten the source.** No cut-to-black between sections, no jump-cuts to remove pauses, no playback-rate changes. The viewer sees the full take.

**Verification (do this every time before handing off):**

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 source.mp4
```

Confirm: root `data-duration` ≥ that value. `<video>` `data-duration` ≥ that value. `<audio>` `data-duration` ≥ that value. Any shorter = audio is being clipped = bug, fix immediately.

**If Marlon says "you cut my video" or "you're cutting off my words":**

Don't get defensive — but also don't blindly assume you trimmed something. Most often the actual cause is **MG coverage too high**: when MG covers ~90% of the video, captions are skipped during MG windows, so ~90% of the spoken words have no visible captions, which makes the words feel visually missing even though the audio is intact. Verify durations with `ffprobe` first; if they're correct, the fix is reducing MG coverage (see the next section), not editing the source.

If a request would require trimming the source ("can you cut the part where I stumble", "remove the dead air at 0:42") — stop and tell Marlon that's outside the skill's scope. He should re-record or hand you a pre-trimmed source. Never make an edit decision unilaterally.

## Hard rule: never render without explicit approval

After lint + inspect pass, **start the studio editor (`npx hyperframes preview`) and stop**. Hand Marlon the localhost URL and wait for feedback. Iterate (edit → save → re-lint → he refreshes) until he says "good to render." Only then run `npx hyperframes render`. A render takes 5–10 minutes and burns the cache window — never trigger one speculatively.

## Hard rule: never build anything before Marlon approves the combined plan

The combined plan (cutaways + MGs in one markdown table) is the ONLY gate. Past it, kie.ai calls cost money and HTML changes burn time. Before it, no generation, no HTML.

1. Read transcript → apply the assignment rule (concrete=cutaway, abstract=MG) → propose ONE combined markdown table in chat (format: `references/combined-plan-template.md`). Cutaway rows include image description + on-image text quoted; MG rows include the full eyebrow/headline/sub/footer copy.
2. **Stop.** Wait for Marlon to either edit rows inline or say "go".
3. Only then: serialize cutaway rows to `image-plan.json`, run `python3 scripts/generate_images.py`, and start writing the HTML using the MG rows as the locked spec.

Never speculate-generate "to see what it looks like". Never regenerate all cutaways on every iteration — use the script's idempotency (only `--force` re-fetches existing PNGs). Never write composition HTML before approval.

## Hard rule: render dimensions equal source dimensions

Always. The render output's width × height (verified by `ffprobe`) must match the source's width × height exactly. The composition's root `data-width`/`data-height` is set from `ffprobe` on `source.mp4` in workflow step 1 — never hard-coded. Image PNGs from kie.ai are generated at the same aspect ratio (auto-mapped by `generate_images.py`) and CSS-fit with `object-fit: cover` so they fill the frame even if the model returns a slightly different pixel size.

## Read this first: the operating principle

Marlon's videos are direct-response **talking-head** ads. The face is the product — viewers watch because they want to see and trust the person on camera. Reference style: Hormozi / Iman Gadzhi / Mosri. **MG is icing on the cake, not the cake.** A finished ad is mostly Marlon talking with captions, with brief MG bursts that punctuate specific narrative pivots. The default is "speaker on screen" and MG is the exception.

Three principles that all the rules below derive from:

1. **The face creates trust. The speaker is the spine of the ad.** The viewer should keep returning to the face — but no fixed coverage % is prescribed. Speaker share emerges from cadence + beat-length rules below. What matters is *distribution*: the speaker is never left alone on screen for more than **8 seconds at a stretch** after t=10s. Long ghosted stretches where the viewer can barely see Marlon defeat the entire point of a talking-head ad.
2. **Captions are the fallback for sound-off scrolling.** Most Facebook viewers watch muted on first scroll. Captions must be readable, on-brand, and never cover the speaker's face. They are visible during ALL speaker-only stretches.
3. **Motion graphics punctuate, they don't decorate.** Each one lands on a narrative pivot (a niche reveal, a contrast, a stamp, a payoff, a CTA). Brief — 1.5–5s typically. If a beat doesn't have an underlying narrative reason, don't add it. If you're tempted to add a beat just to "fill space" — that's the bug, leave the speaker alone.

When MG IS active, the speaker stays *ghosted* in the background at **~55% opacity** with a **light dim overlay (~50–60% alpha)** so they're clearly visible, not a vague silhouette. Marlon validated 22% was too dim and 90% MG coverage was unwatchable.

## Pre-build interview (always do this)

Before writing any HTML, get answers to these. If the user already gave some answers in the conversation, just confirm — don't re-ask. Missing answers cause rework.

| Question | Why it matters | Default if user says "you decide" |
|---|---|---|
| **Where will it run?** Facebook feed, Instagram Reels, both? | Facebook feed crops 9:16 to 4:5 (top/bottom 285px sacrificed). The safe-zone constraint changes the layout. | Both — design for 9:16, enforce 4:5 safe zone. |
| **What's the source aspect ratio?** | If 9:16 already, no fitting needed. If 16:9 or square, need to letterbox / blurred-bg fill. | Probe with `ffprobe` — assume 9:16 if dimensions are 1080×1920. |
| **Where's the speaker's head in frame?** | Captions and lower-third MG must never cover the head. | Assume head is in upper-center; place captions at `bottom: 560px`. |
| **Is there a transcript, or should I auto-transcribe?** | Word-level timestamps drive both captions and MG beat alignment. | Auto-transcribe with `npx hyperframes transcribe --words` (see `references/workflow.md`). |
| **Who's the audience?** | Drives MG palette tone — pain/solution colors. | Assume healthcare practice owners (dentists, chiros, podiatrists, PTs) unless specified — use the default palette below. |
| **Is there a call-to-action in the script?** | Determines whether the final MG is a CTA + benefits block or just a closing stamp. | Detect a CTA phrase in the transcript ("click below", "watch the training", "book a call"). If present, build a CTA block; if not, end with a closing stamp. |

If the user says "you decide" or similar, take the defaults and proceed. If they want a non-default audience or palette, get the colors before writing CSS — don't draft and rework.

## The 4:5 safe zone (HARD CONSTRAINT — overrides everything else)

Source: 1080 × 1920 (9:16). Facebook crops to 1080 × 1350 (4:5) — losing **285px from the top and 285px from the bottom**.

- **Safe zone:** y = 285 → 1635, x = 0 → 1080.
- **Working band (with breathing room):** keep readable content inside **y = 350 → 1570** — not jammed against the safe-zone edges. The 65px buffer on each side absorbs minor layout shift and platform-specific cropping (Facebook feed, Reels overlay UI, Instagram Stories chrome).
- This rule **overrides** every other placement preference, including the head-clearance preference below. **Captions and motion-graphic content must NEVER cross y = 285 (top) or y = 1635 (bottom).** This includes the bottom of multi-line caption groups and the full vertical extent of the tallest MG block.
- Speaker's head sits in the upper portion of the safe zone (typically y ≈ 400–900).
- Captions: position at `bottom: 560px` — caption block sits centered around y ≈ 1300, well inside the safe zone, well clear of the head.

### MG placement (ONE HARD RULE — no exceptions, no tiers, no loopholes)

**Every MG block — list, card, chip, stat, stamp, CTA, eyebrow+headline+sub block, single giant word, anything — anchors at `top ≥ 960`. The lower half of the safe zone is the ONLY zone for motion graphics.**

This is non-negotiable. There is NO "above the head" placement, NO "takeover stamp" tier, NO "full-screen takeover" loophole. Marlon's head sits at y ≈ 400–900 — any block at `top < 960` covers his face. The face is the trust anchor; covering it kills the ad.

**Why this is more aggressive than it sounds.** Previous skill versions had a tier-2 "above the head, top: 350–500" allowance for "single giant stamps" like "BY DESIGN". Agents abused it: any beat with a big number or short phrase got promoted to tier 2, and the result was multi-element blocks (eyebrow + giant headline + subtitle) sitting directly on the speaker's face. Marlon flagged this on Ad_1 ("A NEW WAY IN / 2026 / HOW PATIENTS FIND YOU" landed across his head at t≈7s). The tier is now deleted.

**Big stamps stay big — they just live below the chest.** A "2026" or "BY DESIGN" or "100% YOURS" stamp can still be 200–280px font, dominate the lower half, and read as a takeover moment. It just doesn't sit on the face. Center it horizontally, anchor at `top: 1080–1200` depending on stamp height.

**If your content doesn't fit at `top ≥ 960`:**

1. Drop the eyebrow if it's redundant with the headline.
2. Reduce headline font size (130→110→90→70).
3. Reduce row body font size (38→32→28→24).
4. Reduce row gap (22→14→10) and padding (24→18→12).
5. Drop a row or merge two rows into one.
6. Drop the eyebrow.
7. Drop the entire beat (captions already cover what the speaker is saying).

If after all seven you still overflow past y=1570, the beat is too dense for this placement — drop it. **Never raise `top` below 960 to "make room"** — that's the bug pattern.

**Per-block dark plate (REQUIRED).** Since the speaker stays at full brightness end-to-end (no global curtain — see `feedback_no_curtain_during_mg`), every MG block needs its OWN background plate so the copy reads against the bright video. Use a rounded semi-opaque dark card sized to the content:

```css
.mg-plate {
  background: rgba(10, 10, 14, 0.82);
  border: 3px solid rgba(255, 255, 255, 0.08);
  border-radius: 28px;
  padding: 28px 36px;
  box-shadow: 0 18px 0 rgba(0, 0, 0, 0.55);
}
```

Tune the alpha (0.75–0.92) per beat. Solid color plates (red for pain, green for solution, yellow for CTA at lower alpha) are also fine — Hormozi-style. Never let MG text sit directly on bright video with no plate.

**Verification:** after any MG layout change, run `npx hyperframes inspect --at <hero-frame-timestamps>` AND visually check the studio at the same timestamps. Inspect catches safe-zone violations; visual check catches "block at top:740 covers the speaker's face" (inspect misses this — the safe zone is technically respected, but the face is hidden). **For every MG hero frame, screenshot the studio and confirm: speaker's face is fully visible above the MG block.** If the face is covered, the placement is wrong, full stop.

**Rule of thumb when reviewing your own draft:** for each MG block, ask "could I push this down 200–400px and have it still fit?" If yes, push it. The most common mistake is anchoring at top:700 by reflex when the content would have fit at top:1000.

**Always verify with `npx hyperframes inspect --at <hero-frame-timestamps>`.** Inspect catches blocks crossing the safe zone. Run it after every layout change.

**The CTA should sit below the head.** The close-out is high-trust real estate — the speaker's face matters here. If the CTA block is too tall to fit below the head, shrink the bullets / shorten the headline rather than covering the face.

Decorative elements (background gradients, faint ornament lines) can extend outside the safe zone, but anything the viewer needs to read can't.

When linting, run `npx hyperframes inspect` at hero-frame timestamps. Zero layout issues = safe zone respected.

## Hormozi-style captions (the default)

Marlon's confirmed style. Don't deviate without explicit instruction.

```css
font-family: "Archivo Black", "Anton", sans-serif;
font-weight: 900;
font-size: 96px;
letter-spacing: 0.005em;
text-transform: uppercase;
color: #FFFFFF;
-webkit-text-stroke: 9px #000000;
paint-order: stroke fill;
text-shadow: 0 8px 0 rgba(0,0,0,0.95), 0 0 28px rgba(0,0,0,0.85);
```

- **Group size:** 3 words max per caption. Break on terminal punctuation, comma, or pauses ≥ 300ms.
- **Active-word pop:** the currently spoken word turns yellow `#FFE500` and scales to 1.16 over 70ms (`back.out(2.6)`), then settles back to white at scale 1 over 180ms.
- **Entrance:** scale 0.78 → 1, opacity 0 → 1, y 14 → 0, duration 0.14s, ease `back.out(2.4)`.
- **Exit + hard kill:** opacity 0 over 100ms before group end, then `tl.set(sel, { opacity: 0, visibility: "hidden" })` exactly at `group.end` — this is non-negotiable, prevents the previous caption flashing under the next one.
- **During motion graphics: captions hide — and not just via a parent opacity fade.** Marlon validated that parent-only fade is unreliable in the studio. Use **both** mechanisms together:
  1. Fade the parent `#captions` container to opacity 0 at MG start and back to 1 at MG end (visual safety net).
  2. **Skip per-group tween creation entirely** for any caption group whose start time lands inside an MG window. The DOM element exists but never gets entrance / word-pop / exit tweens — it stays at its initial `opacity: 0; visibility: hidden` state for the whole timeline. This is the bulletproof part.

  ```js
  const inMgWindow = (t) => MG_PERIODS.some(p => t >= p.s && t < p.e);
  groups.forEach((g, gi) => {
    // ... build & append the group element ...
    if (inMgWindow(g.s)) return;  // skip: no tweens at all for this group
    // ... normal entrance + word-pop + exit tweens ...
  });
  ```

  Don't ship without the skip-check. Captions visible over MG copy is the most common bug reported on first preview.

### Caption container layout (DO NOT GET WRONG — captions silently disappear if this is off)

Multiple cap-groups live in the DOM at once, each toggled visible/hidden by the timeline. They must **stack on top of each other** (not push each other down the page) and they must **anchor to a fixed y position** so the caption block sits where you put it regardless of how many words are in the current group. The pattern that works:

```css
#captions {
  position: absolute;
  left: 0; right: 0;
  bottom: 560px;       /* the y-anchor for the caption block */
  height: 0;           /* zero-height stage; cap-groups extend up via bottom:0 */
  pointer-events: none;
  z-index: 5;
}
.cap-group {
  position: absolute;
  left: 0; right: 0;
  bottom: 0;           /* anchored to the stage's bottom edge */
  display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-end;
  gap: 16px 22px;
  padding: 0 60px;
  opacity: 0; visibility: hidden;
  transform-origin: 50% 100%;
}
```

**Why each line matters — don't drop any of these:**

- `#captions { height: 0 }` — without an explicit height, an absolute element whose only children are also absolute collapses to height 0, which is fine, but only if you also anchor each `.cap-group` with `bottom: 0`. If you don't, the cap-groups render at the parent's top-left (y of the anchor) and either drift off-screen or land in the wrong row.
- `.cap-group { position: absolute; left: 0; right: 0; bottom: 0 }` — all three needed. `position: absolute` makes them stack instead of pushing. `left/right: 0` gives the inner flex a width to center words within. `bottom: 0` pins the caption block's baseline to the stage anchor.
- **Never** make `#captions` itself `display: flex` while also making cap-groups `position: absolute` with no `top/left/right/bottom` set — that combination renders captions at an undefined location and they vanish during speaker-only stretches. (This bug shipped once; the symptom is "captions only show during MG beats" or "captions never show at all.")

After any change to caption layout, scrub the studio at a known speaker-only timestamp (e.g. 7s, 18s, 42s, 55s in a typical 80s ad — anything between MG windows) and confirm captions are visible. `inspect` won't catch this — captions still pass safe-zone checks even when their layout is broken, because the words are technically inside the safe band.

The helper script at `scripts/build_caption_groups.py` reads a HyperFrames transcript and produces the `groups.json` array ready to embed in the composition. Use it — don't hand-write groups.

## Motion graphic system: ghosted speaker + variable beats

The mechanic Marlon validated:

- **Video stays clearly visible** behind motion graphics. Drop video opacity to **~0.55** (NOT 0, NOT 0.22). At 0.55 the speaker reads as a real person on screen, not a faint ghost.
- **Use a light dim overlay** between the video and the MG content — a radial-ish gradient with alpha around `0.45–0.60` (NOT solid). This takes the edge off the video brightness so the MG copy pops, without obliterating the speaker.
- **Concrete starting values that work:**
  ```css
  /* curtain */
  background: radial-gradient(ellipse at 50% 50%, rgba(20,20,28,0.45) 0%, rgba(5,5,5,0.65) 80%);
  ```
  ```js
  /* tween */
  tl.to("#a-roll", { opacity: 0.55, ... }, p.s);
  ```
  Tune from here — never go below ~0.45 video opacity.
- **MG content prefers the lower half of the safe zone — keep the speaker's head clear.** Default to anchoring MG blocks at `top: 900–1100px` so the face stays visible above. Only cover the head when the content genuinely doesn't fit below. This applies especially to the CTA block — the speaker's face during the close-out is high-trust real estate; don't bury it under bullets.
- **Captions hide** during MG windows (parent container opacity → 0).
- **Audio NEVER fades.** The voice is the spine. Audio runs from `0` to end of clip, untouched.

### Timing — anchor every MG to its spoken words (HARD RULE)

The most common shipped bug is MG that enters before the lead-in finishes and exits as the punchline begins — the speaker says a word and the corresponding visual is already gone. Every MG window must be timed off the transcript:

1. **Entrance — on the word.** Each sub-element's GSAP tween starts AT the corresponding spoken word's start time (not before, not after). The ~0.15-0.3s `back.out` ease completes just after the word is said, so it reads as a sync'd visual punch. Don't lead with eyebrow before the speaker says the eyebrow phrase; don't drop the headline in mid-buildup.
2. **Exit — 0.7s past the LAST relevant word.** The MG window holds for ≥0.7s after the last spoken word the MG visually represents — including any **footer** phrases that mirror trailing speaker lines. Compute `p.e = last_word_end + 0.7`. (0.7s = ~3 word-reads of dwell time without going stale.)
3. **Footer text animates in as a block** the moment its first corresponding spoken word lands. Never word-by-word — captions already do that and word-by-word footer competes.
4. **Window start = first relevant word's `start`.** Don't pre-buildup. If the eyebrow says "Their entire business model", `data-start` = the moment "Their" starts.
5. **Adjacent beats must MERGE into one MG window** when there's no speaker-only breath between them. Bouncing the curtain between back-to-back payloads strobes the speaker's brightness AND forces you to violate the 0.7s tail rule. Instead: one continuous curtain, content cross-fades inside.

**Workflow when timing a beat list:**
- For each beat, write the **first relevant word's start** and the **last relevant word's end** in the comment.
- Compute `data-start` and `data-duration = (last_end + 0.7) - data-start`.
- Walk the beat list — wherever `next.start < prev.end + 0.7`, merge into one `MG_PERIODS` entry and cross-fade content inside the same continuous curtain.

**Concrete example (Ad_5 Beat 2 — what NOT to do, then the fix):**

> **Wrong:** `{s: 16.0, e: 19.0}`. The footer "THAT'S HOW THEY PAY RENT & STAFF" exits at 19.0 — but speaker says "rent" at 19.75 and "staff" at 21.18. Visual disappears as words are spoken.
>
> **Right:** Last relevant word is "staff" ending at 21.72. New `e = 21.72 + 0.7 = 22.42`. Footer enters at 18.88 (when "That's" starts) as a block, not word-by-word. If next beat starts before 22.42, merge.

### MG coverage budget and pacing (HARD)

**Combined visual coverage target: ≤35% of source duration**, split as **MG ≤25% + cutaway ≤15%**. The reference style (Hormozi / Iman Gadzhi / Mosri) keeps the speaker on screen most of the time, *interrupted often* by short visual beats — not punctuated rarely by long ones.

| Constraint | Number | Why |
|---|---|---|
| MG coverage | **≤25% of runtime** | Stamps/chips/lists/CTA share this bucket |
| Cutaway coverage | **≤15% of runtime** | B-roll, full-frame images, reaction zooms — a separate bucket so cheap cutaways don't eat the MG budget |
| Combined coverage | **≤35% of runtime** | At >40% the speaker disappears and the ad reads as a slideshow |
| **Max speaker-only stretch** | **≤8s after t=10s (BLOCKING)** | Industry: >4s static = danger zone, >8s = scroll. The opening hook (0–10s) is exempt so the face can carry it |
| Single MG burst length | **stamps/chips 1.5–3s, lists 3–5s, CTA 5–7s** | Anything longer = cut content, not extend window |
| Cutaway hold | **0.8–2.0s typical, ≤3s hard** | Vertical short-form b-roll norm; keeps cadence tight |
| Gap between beats | **≥2.5s of clean speaker** | Re-anchors on the face without leaving dead air |
| Cadence | **8–12 distinct visual beats per minute** | One every 5–7s. Below 8 reads as static; above 12 strobes |
| **First MG entry** | **NEVER before t=5s. Default 5–7s.** | Opening hook lands on the face; an MG opener gets scrolled past |

**This is a workflow gate.** After identifying narrative pivots from the transcript, build a beat budget table BEFORE writing any HTML and verify it sums to ≤35%:

```
| Beat | s     | e     | duration | type            |
|------|-------|-------|----------|-----------------|
| 1    | 6.27  | 11.84 | 5.57     | full-frame list |
| 2    | 16.0  | 19.6  | 3.60     | stamp           |
| 3    | 33.13 | 39.1  | 5.97     | 3-row list      |
| 4    | 84.96 | 91.7  | 6.74     | CTA             |
| Total|       |       | 21.88    | / 91.77 = 24%   |
```

If the table exceeds the budget, **drop beats** — don't shrink them. Drop priority order:
1. Mid-video "stamp" beats that just re-state what the speaker is already saying clearly (captions cover this).
2. Compound triplets in the middle that visualize lists the speaker enumerates verbally.
3. Adjacent merged beats (collapse two payloads into one shorter beat that captures the punchline of both).

Keep:
1. **The CTA** (always — it converts).
2. **One opening niche/hook beat** if the script names the audience ("if you run a dental practice...").
3. **One "big number" or "big stamp" moment** if the script has a payoff line ("100% yours", "by design", a specific stat).

Most 60–90s talking-head ads land at **3–5 beats total**. Six is a lot. Eight is too many.

### How many beats?

**As many as the narrative justifies WITHIN the 30–35% budget — usually 3–5 for a 60–90s ad.** Don't pad. Don't strip below 3 unless the source is <40s. Read the transcript and look for narrative pivots:

- **Niche reveal** — when the speaker names who the video is for ("if you run a dental practice, a chiropractor clinic…")
- **Contrast / conflict** — pain vs. solution, them vs. us ("they get paid when you keep paying" / "we refuse to run that model")
- **Stamps / accusations** — short, punchy claims that should land like a fist ("by design", "we refuse")
- **Lists / triplets** — three things stacking (every blog → authority, every review → trust, every photo → local signal)
- **Payoff numbers** — "100% yours", "$50k a month", "12 patients a week"
- **CTA + benefits block** — closing 8–12 seconds, what they'll see when they click

Aim for a roughly even rhythm of speaker-only / speaker-with-chip / speaker-ghosted-behind-full-MG. If three full-frame MG beats fire back-to-back with no breath in between, the face disappears for too long — break them up.

### Two MG patterns

| Pattern | Use for | Video opacity | MG layout |
|---|---|---|---|
| **Ghost** (default) | Big narrative beats: niche reveal, full contrast, compound system, payoff, CTA + benefits | ~22% with dark gradient overlay | Full-frame, content centered in safe zone |
| **Overlay** | Quick callouts: a single number, a 2-second word stamp, a side label | 100% (no fade) | Corner chip, lower-third bar, or floating element — *outside* the head's bounding box |

For each beat, pick the pattern that matches the narrative weight. If unsure, default to Ghost.

### Default palette (healthcare audience)

Pain / problem beats: **`#FF3B3B`** (red)
Solution / payoff beats: **`#22D27C`** (green)
CTA + emphasis: **`#FFE500`** (Hormozi yellow)
Canvas / dim layer: **`#0A0A0A`** (near-black)
Body text on dim: **`#FFFFFF`**

For other audiences, ask before drafting CSS.

### Typography

- **Anton** — display headlines in MG (uppercase, condensed, weight 400)
- **Archivo Black** — captions, big stamps, "100% YOURS" type moments (weight 900)
- **Inter** — small labels, taglines, bullet body (weights 600 / 800)

The HyperFrames compiler embeds these automatically — just declare them in CSS.

## Cutaways and motion graphics — the combined visual system

The skill has two visual treatments that punctuate the speaker:

- **Cutaway image** — full-frame still that **fully replaces the speaker** for 1.5–3s. Generated by kie.ai `gpt-image-2` at 1K, sized to source aspect ratio. Track-index 2, fades in/out via GSAP. Audio underneath never changes.
- **Motion graphic** — text/layout block over a ghosted speaker (~55% video opacity, light dim overlay). Built in HTML/GSAP. Speaker visible, face holds trust.

They are NOT interchangeable. Each is the right tool for a different *kind* of beat. (Validated by Mayer's Cognitive Theory of Multimedia Learning: visual + verbal must converge on meaning; when they duplicate, they cost cognitive load instead of adding to it.)

### The assignment rule (decides cutaway vs MG for every beat)

| Beat is about... | Use | Why |
|---|---|---|
| A **concrete thing** the speaker names (map, real chart, screenshot, photo, place, product) | **Cutaway image** | Image *shows* the thing — text alone can't substitute |
| An **abstract claim, number, list, or stamp** | **Motion graphic** | Kinetic typography is the workhorse for direct-response clarity (research-validated). Speaker stays ghosted, face holds trust. |
| The **CTA** at close | **MG always** | Speaker face must be visible (ghosted) during the conversion ask — a cutaway here removes the trust anchor at the worst moment |
| The **25–35s pattern interrupt** | **Cutaway preferred** | The drop-off cliff demands the biggest visual change. Speaker → cutaway is more abrupt than speaker → ghosted+MG. Use the heaviest tool exactly here. |

Concrete examples:
- "ranking #1 in Sydney" → **cutaway** (rank map with pins)
- "we doubled their revenue" → **cutaway** if a real client chart, **MG** if a generic "+118%" stamp
- "100% YOURS" / "BY DESIGN" / "WE REFUSE" → **MG** (abstract claim)
- "click below" / "book a call" → **MG** (CTA, always)
- "three things every clinic gets wrong" → **MG** (list/triplet)
- "this is what their patient inbox looks like" → **cutaway** (a thing, screenshot)

### No double-encoding (HARD)

If the speaker says "$50K a month" and a cutaway stat-card already shows "$50K" on screen, do NOT also fire an MG stamp with "$50K". The image already encodes the claim visually; the MG would just duplicate. Mayer's redundancy principle: redundant visual + visual + audio costs cognitive capacity instead of adding clarity. **One channel per claim.** Never overlap a cutaway and an MG in the same time slot.

### Rotation rhythm (default sequencing)

A clean 60–90s ad rotates through three states:

```
speaker → MG → speaker → cutaway → speaker → MG → speaker → cutaway → speaker → CTA(MG)
```

Rules:
- **Never two cutaways in a row.** ≥2.5s of speaker (or ghosted+MG) between cutaways. Two cutaways back-to-back kills the talking-head premise — viewers need the face to recover.
- **Never two MGs in a row without a speaker beat.** If two narrative beats are both MG-shaped, merge them into one continuous MG window with a content cross-fade (existing pattern).
- **Always open on face.** First 5s = speaker + caption only. No cutaway, no MG.
- **Always close on face.** CTA is an MG (face ghosted, visible) — never a cutaway.

### What neither tool is for

- Decorating speaker-only stretches that read fine on their own
- Filling silence — silence is the speaker's pacing, leave it alone
- Restating something the previous beat already covered

### The combined approval workflow (HARD)

One table, both kinds, reviewed together before anything is generated or built. This is the single gate — past this point, generation costs money and HTML gets written.

1. Read the transcript. Identify every narrative beat that justifies a visual punch. Apply the assignment rule to decide cutaway vs MG for each.
2. Build the **combined plan** as a markdown table in chat — one row per beat, sorted by timestamp, with full MG copy spelled out (eyebrow / headline / sub / footer) and full cutaway descriptions. Format: `references/combined-plan-template.md`.
3. **Stop.** Show Marlon the table with: *"Reply with edits to any row, or say 'go' to build."*
4. On "go":
   - Serialize the cutaway rows (`kind == "cutaway"`) to `image-plan.json` at the project root.
   - Run `python3 .claude/skills/how-to-edit-videos/scripts/generate_images.py image-plan.json --source source.mp4` — only cutaway rows hit kie.ai.
   - Use the MG rows as the spec for HTML authoring. Copy, types, palettes, and timestamps are now locked in.
5. Verify each PNG matches source dimensions before wiring into the composition.

**Iteration:**
- Cutaway re-do: edit that row's description in `image-plan.json`, re-run with `--force` (the script is idempotent — only the changed id refetches).
- MG copy change: edit the row in chat or directly in HTML — no API call needed.

**Never** call kie.ai or write composition HTML before the combined plan is approved. The whole point of the gate is that Marlon sees both kinds together and edits as one document.

### Image elements in the composition

```html
<img class="story-image"
     id="img-rank-map"
     src="images/rank-map.png"
     data-start="12.4"
     data-duration="3.2"
     data-track-index="2"
     data-z-index="4">
```

```css
.story-image {
  position: absolute;
  inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;     /* fills frame regardless of model's exact pixel size */
  opacity: 0;            /* tweened in/out by GSAP */
  z-index: 4;            /* above #a-roll (video), below #captions */
  pointer-events: none;
}
```

```js
// Per image: fade in 0→1 over 0.18s on entry, 1→0 over 0.18s on exit.
IMAGE_PERIODS.forEach(p => {
  tl.to(`#${p.id}`, { opacity: 1, duration: 0.18, ease: "power2.out" }, p.s);
  tl.to(`#${p.id}`, { opacity: 0, duration: 0.18, ease: "power2.in" }, p.e - 0.18);
});
```

### Captions during image windows

Same hide-mechanism as MG windows. The `inMgWindow` skip-check that prevents caption tweens during MG must be **extended to also test image windows** — easiest pattern is to union both arrays into one `VISUAL_PERIODS`:

```js
const VISUAL_PERIODS = [...MG_PERIODS, ...IMAGE_PERIODS];
const inVisualWindow = (t) => VISUAL_PERIODS.some(p => t >= p.s && t < p.e);
groups.forEach((g, gi) => {
  // ... build & append the group element ...
  if (inVisualWindow(g.s)) return;  // skip: no tweens at all for this group
  // ... normal entrance + word-pop + exit tweens ...
});
```

Also fade `#captions` parent to 0 at every image-window start and back to 1 at end (visual safety net, same as MG).

### Image-specific rules

- **Always full-frame** — no picture-in-picture, no corner thumbnails. Image fully covers the speaker.
- **Aspect ratio matches source** — `generate_images.py` auto-derives from `ffprobe`. Never hard-code.
- **Resolution = 1K** — Marlon's standing rule (lowest cost, decodes fast in studio).
- **Audio uninterrupted** — never modify the `<audio>` element when adding images. Same source-immutability rule as MG.
- **Text on image is fine and encouraged** — graphs, stat callouts, headlines on the image itself help tell the story. Describe text exactly in the plan row.
- **No photoreal humans on images** — they steal trust from the speaker and drift uncanny. Stick to icons, charts, glyphs, simplified illustrations.
- **No real logos / brand names** — moderation flags + not ours to use.

## Cadence + combination rules

Research consensus for short-form vertical ads in 2025/2026 (Buttercut, Visla, Buffer, AIR Media-Tech, todaymade, NCSU on Mayer's Cognitive Theory, Stackmatix, Joyspace):

- 0–3s = **71% of retention decision** → never open on cutaway/MG; open on face + promise
- 3–30s window → visual change every **8–12s**
- **Mandatory pattern interrupt at 25–35s** — and it should be a **cutaway**, not an MG (drop-off cliff demands the biggest possible visual change)
- 35s–end → visual change every **15–25s**
- Always close on face — CTA is an MG (face ghosted, visible), never a cutaway

The skill enforces a **split budget** — MG ≤25% and cutaway ≤15%, combined ≤35%. Separate buckets so adding cheap short cutaways doesn't eat the MG budget.

| Rule | Value | Notes |
|---|---|---|
| Open the video | Always speaker + caption | Never open with cutaway or MG |
| First visual beat (cutaway OR MG) | ≥ 5s, default 5–8s | Hook lands on the face |
| **Cutaway duration** | **0.8–2.0s** typical, ≤3s hard | Vertical short-form b-roll norm; keeps cadence tight |
| MG duration | stamps 1.5–3s, lists 3–5s, CTA 5–7s | Existing tiers — research-aligned |
| **MG bucket** | **≤25% of runtime** | Stamps, chips, lists, CTA |
| **Cutaway bucket** | **≤15% of runtime** | B-roll, full-frame images, reaction zooms |
| **Combined coverage cap** | **≤35% of runtime** | Sum of MG + cutaway buckets |
| Gap between any two visual beats | ≥ 2.5s clean speaker | Spans cutaway↔cutaway (face recovery), MG↔MG, cutaway↔MG |
| **Max speaker-only stretch** | **≤8s after t=10s (BLOCKING)** | Industry: >4s static = danger zone, >8s = scroll |
| **25–35s pattern interrupt** | mandatory; **cutaway preferred** | The drop-off cliff — biggest available visual change |
| Total visual moments per minute | **8–12** | Below 8 reads static; above 12 strobes |
| Two cutaways in a row | **Never** | Face must recover before another full takeover |
| Two MGs in a row without speaker beat | **Never** | Merge into one continuous MG window with cross-fade |

### Opening visual budget (HARD — front-loading rule)

The visual budget is **not evenly distributed across the runtime.** Drop-off is front-loaded, so the visual punctuation must be too. For any ad ≥ 60s:

| Section | Share of total visual beats | Why |
|---|---|---|
| **0–30s (front third)** | **≥ 40% of beats, minimum 3 beats** | Drop-off cliff lives here; needs the most pattern interrupts |
| 30s–end | The remainder, including CTA | Audience is more stable; coverage can stretch |

**First-30s gate (BLOCKING):** if the combined plan has fewer than 3 visual beats with `s < 30`, the plan fails. Add beats to the front before writing HTML — do not advance to generation.

**Max-stretch gate (BLOCKING):** for every adjacent pair of beats with `s >= 10`, if `next.s − prev.e > 8.0`, the plan fails. Insert a short cutaway (0.8–2.0s B-roll, image, or reaction zoom) into the gap. Speaker is never alone for more than 8 seconds at a stretch after t=10s.

**Cadence gate (BLOCKING):** total beats / (runtime_seconds / 60) must be ≥ 8. Below that, the ad reads as static — add beats before generation.

The single most common mistake on this skill is back-loading: agents put the niche-reveal MG at 5s, then nothing until the system MG at 50s and CTA at 75s. That leaves 0–30s naked, the most fragile window, with the speaker carrying it alone. Captions are not a substitute for a visual beat — they're the floor, not the ceiling.

**Default opening cadence (windows are GUIDES, not slots).** The actual placement always anchors to a real narrative pivot in the transcript and follows the assignment rule (concrete=cutaway, abstract=MG). Use these windows to *check coverage*, not to fabricate beats:

- Around **5–10s** — look for the hook / niche-reveal / promise → likely MG
- Around **10–20s** — look for the first concrete thing the speaker names → likely cutaway
- Around **20–35s** — the mandatory pattern interrupt; cutaway preferred if there's a concrete referent, MG otherwise

If a window has no real pivot to anchor to, **leave it empty — do not invent a beat to fill the window**. The failure mode this rule guards against is back-loading (3 visual beats clustered after t=45s with nothing before), not "exactly one beat per window." If two of these three windows have nothing AND the transcript clearly contains pivots in them, you are under-served on the front and must add beats.

### Combined beat budget table (the workflow gate)

After identifying narrative pivots and applying the assignment rule, build ONE combined table and verify the gates BEFORE writing any HTML or calling kie.ai:

```
| Beat | s     | e     | duration | kind    | type            |
|------|-------|-------|----------|---------|-----------------|
| 1    | 6.27  | 8.7   | 2.43     | cutaway | rank-map        |
| 2    | 16.0  | 19.0  | 3.00     | mg      | stamp           |
| 3    | 31.0  | 33.5  | 2.50     | cutaway | revenue-graph   |  ← 25–35s interrupt = cutaway ✓
| 4    | 50.5  | 53.5  | 3.00     | mg      | list            |
| 5    | 64.8  | 67.0  | 2.20     | cutaway | stat-card       |
| 6    | 84.96 | 91.7  | 6.74     | mg      | CTA             |
| Total|       |       | 19.87    | / 91.77 = 22% — pass |
```

Gates (BLOCKING — fix the plan, don't write HTML against a failing budget):
- Sum ≤ 35% of source duration
- First beat ≥ 5s
- Every gap ≥ 3s of clean speaker
- 25–35s window contains at least one beat (cutaway preferred)
- No two cutaways in a row
- Per-stretch length within limits (cutaway 1.5–3s, MG stamp 1.5–3s, MG list 3–5s, MG CTA 5–7s)
- CTA is `kind == "mg"` (never a cutaway)
- Rotation rhythm: walk the list, never see two `cutaway` rows back-to-back
- **First-30s gate: ≥ 2 visual beats with `s < 30`** (front-loading rule — see above)

**Drop priority when over budget:**
1. Redundant MG stamps that re-state what captions already cover (no double-encoding)
2. Decorative cutaways that don't visualize a specific concrete thing
3. Adjacent same-kind beats merge into one
4. **Never drop:** the 25–35s interrupt, the opening niche reveal (if present), the closing CTA

## Workflow (every project)

1. **Probe the source video.** `ffprobe -v error -show_entries stream=width,height,duration -of default=nw=1 source.mp4`. Confirm dimensions and duration. **Set the composition's root `data-width`/`data-height` from this output — never hard-code 1080×1920.** Render dimensions must equal source dimensions.
2. **Scaffold a project.** `npx hyperframes init --here --no-install` inside a fresh folder, or copy the `ad-marketing-truth/my-video/` structure. Drop the source video in as `source.mp4`.
3. **Transcribe.** `npx hyperframes transcribe source.mp4 --words --out transcript.json`. Confirm word count looks right relative to duration.
4. **Build caption groups.** `python3 scripts/build_caption_groups.py transcript.json > groups.json` (script bundled with this skill).
5. **Read the full transcript and apply the assignment rule.** Identify narrative pivots → for each, decide cutaway (concrete thing) vs MG (abstract claim) per the assignment rule. Aim for **3–6 beats total** for a 60–90s ad, rotating cutaway/MG (no two cutaways in a row).
5b. **Propose the combined plan (GATED).** Draft a single markdown table covering BOTH cutaways and MGs in chat — columns per `references/combined-plan-template.md`. Each MG row spells out the full on-screen copy (eyebrow / headline / sub / footer); each cutaway row spells out the full image description and quoted on-image text. Stop. Wait for Marlon to either edit rows inline or say "go". **Never proceed past this step without explicit approval — kie.ai calls cost money and HTML changes burn time.**
5c. **Generate cutaways + lock MG spec (only after approval).** Serialize the cutaway rows (those with `kind == "cutaway"`) from the approved table to `image-plan.json` at the project root. Run:
   ```bash
   python3 .claude/skills/how-to-edit-videos/scripts/generate_images.py \
       image-plan.json --source source.mp4
   ```
   Verify each PNG at `images/{id}.png` opens cleanly. The MG rows are now the locked spec for HTML authoring — copy, types, palettes, timestamps. Re-runs are idempotent; pass `--force` to regenerate a specific cutaway after Marlon revises its prompt.
6. **Combined beat budget gate (BLOCKING).** Verify the gates from "Cadence + combination rules" against the approved table. Sum durations: **if total > 35% of source duration, drop beats until ≤35%.** Verify: first beat ≥ 5s, every gap ≥ 3s, every burst within length limits, 25–35s window contains a beat (cutaway preferred), no two cutaways in a row, CTA is MG, **first-30s gate: ≥ 2 beats start before t=30s** (front-loading rule). If any check fails, fix the beat list before writing HTML.
7. **Write `DESIGN.md`** — short file with palette, typography, safe-zone reminder, and what-not-to-do. The `hyperframes` skill enforces this gate.
8. **Build `index.html`** — see the `ad-marketing-truth/my-video/index.html` reference. Pattern: video element + audio element + MG curtain + MG chips + **image takeovers (`<img class="story-image">`, see "Image elements in the composition")** + captions container, all timed via `data-start` / `data-duration` / `data-track-index`. Every MG block at `top ≥ 960` unless it's a full-screen takeover stamp. Image elements are full-frame (`inset: 0; object-fit: cover`) on track-index 2, fade in/out via GSAP. Update the caption skip-check to use `VISUAL_PERIODS = [...MG_PERIODS, ...IMAGE_PERIODS]` so captions hide during image windows too.
9. **Source integrity verification (BLOCKING).** Run `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 source.mp4` and confirm:
   - Root `data-duration` ≥ source duration
   - `<video>` `data-duration` ≥ source duration AND `data-start="0"`
   - `<audio>` `data-duration` ≥ source duration AND `data-start="0"` AND `data-volume="1"`
   - No `data-end` on video/audio. No volume tweens on audio.
   If any of these are wrong, fix immediately — audio is being clipped.
10. **Lint, validate, inspect** in that order. `npx hyperframes lint` must be clean. `npx hyperframes validate` may produce false-positive contrast warnings for MG elements that are invisible at the validator's sample timestamps — those are safe to ignore. `npx hyperframes inspect --at <hero-frame-timestamps>` should show 0 layout issues.
11. **Open the studio editor for review — DO NOT render yet.** Marlon reviews every composition in the HyperFrames studio before render. Start the preview server in the background and give Marlon the localhost URL to open in a browser:

   ```bash
   npx hyperframes preview          # starts studio at http://localhost:5173 (default)
   ```

   Run this with `run_in_background: true` so the dev server stays up while you wait. After starting it, **stop and report**:
   - The localhost URL (read it from the preview output — port may differ if 5173 is busy)
   - A short summary of what you built (caption count, MG beat list with timestamps, any deliberate choices Marlon should sanity-check)
   - The exact prompt: *"Open the URL above in your browser, scrub through, and tell me what to change. I'll wait — no render until you sign off."*

   **Do not proceed to step 12 until Marlon explicitly approves.** Iterate on the composition (edit `index.html`, re-lint, re-inspect) — the dev server hot-reloads, so no restart needed. Each round of feedback should end with "anything else, or are we good to render?"

12. **Render into a per-source `output/` folder — only after approval.** Each source video gets its own subfolder in `output/`, named after the source file (without extension), so every deliverable stays grouped with the project that produced it.

    ```bash
    STEM="$(basename source.mp4 .mp4)"          # e.g. "Ad_5_The_Truth_About_Marketing_Agencies_V3"
    mkdir -p "output/$STEM"
    npx hyperframes render -o "output/$STEM/${STEM}_v1.mp4"
    ```

    The `-o` flag overrides the default `renders/` directory. Final layout:

    ```
    project-root/
    ├── source.mp4
    ├── index.html
    └── output/
        └── Ad_5_The_Truth_About_Marketing_Agencies_V3/
            ├── Ad_5_The_Truth_About_Marketing_Agencies_V3_v1.mp4
            └── Ad_5_The_Truth_About_Marketing_Agencies_V3_v2.mp4
    ```

    Bump the version on every re-render (`_v2`, `_v3`, …) — never overwrite a previous render. Expect 5–10 minutes for a 90-second video.
13. **Verify the output** with `ffprobe`: **dimensions of rendered MP4 must equal source dimensions exactly** (width × height match), duration ≈ `data-duration` of root composition (≥ source duration). Also verify each `images/{id}.png` matches source dimensions (or close enough that `object-fit: cover` doesn't crop meaningful content).

If `validate` warns about sparse keyframes in the source video, recommend re-encoding before re-rendering: `ffmpeg -i source.mp4 -c:v libx264 -r 30 -g 30 -keyint_min 30 -movflags +faststart -c:a copy fixed.mp4`.

## Reference: the ad-marketing-truth build

The validated reference composition lives at `ad-marketing-truth/my-video/index.html` (relative to the project root). When in doubt, read that file. Specific patterns to copy:

- The `MG_PERIODS` array at the bottom of the script — clean way to declare ghost-mode windows and have the timeline build itself from the data
- The caption self-lint loop — runs through every group, seeks past its end, warns if anything's still visible. Catches the "previous caption flashing under the next" bug.
- The 4:5 safe-zone comment block at the top of the CSS — keep this in every composition as a reminder to whoever edits it next

## Anti-patterns (don't do these)

- **Don't fully fade the video to opacity 0** — black frames read like ad-end on Facebook scroll.
- **Don't dim the video too far** — anything below ~0.45 makes the speaker invisible behind a heavy curtain. Marlon validated 0.55 video opacity + ~0.45–0.6 alpha curtain as the right balance: speaker clearly readable, MG copy still pops.
- **Don't keep captions visible during full-frame MG** — they compete with MG copy for attention. Hide the parent `#captions` container.
- **Don't make `#captions` `display: flex` and put `position: absolute` cap-groups inside without `bottom: 0; left: 0; right: 0`** — captions will silently disappear during speaker-only stretches. See "Caption container layout" above for the correct pattern.
- **Don't cover the speaker's head with captions or lower-third graphics** — captions stay below y=1100, lower-third MG stays in the lower part of the safe zone.
- **Don't run validate's contrast warnings as errors** — most are false-positives where the validator samples MG text against the underlying video at moments those MG elements are opacity:0. Spot-check the actual rendered video.
- **Don't add MG beats just to fill space.** If a stretch of speaker-only audio reads strong, leave it alone.
- **Don't use `Math.random()` or `Date.now()`** — HyperFrames must be deterministic for rendering. Use seeded patterns or finite repeats.
- **Don't write `repeat: -1`** — breaks capture engine. Calculate finite repeats from the duration.

## When the user iterates

Common requests after the first render:

| Request | Fix |
|---|---|
| "Captions show during motion graphics" | Add `tl.to("#captions", { opacity: 0 }, p.s)` and the matching restore at `p.e` inside the `MG_PERIODS.forEach` loop. |
| "Captions are missing during the speaker-only sections" / "I don't see any captions" | Caption container layout is broken. Check `#captions` has `height: 0` (not `display: flex`) and every `.cap-group` has `position: absolute; left: 0; right: 0; bottom: 0`. See "Caption container layout" section. |
| "Speaker disappears too much" | Reduce MG beat count, or convert some Ghost beats to Overlay (keep video at 100%). |
| "Caption covers my face" | Move captions further down (`bottom: 700px+`), or shorten the caption font-size to 80px. |
| "Motion graphics are too small / too big" | Adjust the `top:` value of the chip and the `font-size` of its main text. Always re-run `inspect` after. |
| "Render froze on a video frame" | Source has sparse keyframes — re-encode with the `ffmpeg` command above. |
| "Want to swap the palette" | Change the three accent colors in `DESIGN.md` and find/replace in CSS. Re-run `validate` for contrast. |
| "Re-do the rank-map cutaway" | Edit that row's `description` in `image-plan.json` (or in chat and re-serialize), then re-run `python3 scripts/generate_images.py image-plan.json --source source.mp4 --force`. The script only re-fetches existing PNGs when `--force` is passed; other ids stay cached. |
| "Change the MG copy on the stamp at 0:18" | Edit the MG row in chat OR directly in `index.html` — no API call needed. Update the eyebrow / headline / sub / footer to match. |
| "Add another beat at 0:42" | Add a new row to the combined plan in chat (apply assignment rule for kind), get Marlon's "go". If `kind == cutaway`: append to `image-plan.json`, re-run the generator (idempotent — only the new row hits kie.ai), then add the `<img>` + GSAP tweens + `IMAGE_PERIODS` entry. If `kind == mg`: add the MG block + `MG_PERIODS` entry. Re-verify the combined budget gate. |
| "Image looks wrong / cropped weirdly" | First check the PNG's actual dims with `ffprobe images/{id}.png` — if the model returned an off-ratio image, the prompt's vertical-composition hint may be too weak; tighten the description (e.g. "all key content in the vertical center column"). `object-fit: cover` will crop sides on a too-wide image. |
| "This beat should have been a cutaway, not an MG (or vice versa)" | Re-apply the assignment rule: concrete thing = cutaway, abstract claim = MG, CTA = MG, 25–35s = cutaway preferred. Swap the row's `kind`, regenerate the plan, get re-approval before changing HTML. |
| "Two cutaways feel jarring back-to-back" | That's the rotation rhythm rule firing — never two cutaways in a row. Convert one to MG, drop one, or insert a speaker beat ≥2.5s between them. |
| "Long stretch of just talking, no visual change" | Max-stretch gate firing — no speaker-only stretch may exceed 8s after t=10s. Find the gap (`next.s − prev.e > 8.0`), insert a 0.8–2.0s cutaway (B-roll, image, or reaction zoom) anchored to a concrete word in the speaker's line during that gap. |
| "Opening feels naked / nothing happening at the start / first cutaway is too late" | First-30s gate failing — front-load. Look in the transcript for a hook/niche-reveal in 5–10s (→ MG) and a concrete referent in 10–20s (→ cutaway), anchor each to its real spoken trigger word. Then fund the new beats by trimming any over-long mid-section MG (lists ≥10s are usually trimmable) to stay under the 35% combined budget. Don't fabricate beats where there's no narrative pivot. |

## Final delivery

Always report back with:

- Path to the rendered MP4 as a clickable markdown link
- Resolution + duration verified by `ffprobe`
- File size
- Any warnings (sparse keyframes, validation warnings) that the user should know about
- A one-paragraph summary of what was built (caption count, MG beat count, total MG duration vs speaker-only duration)

The output is a Facebook ad. The user is going to spend money pushing it to viewers. Treat the deliverable like that — verified, documented, ready to upload.
