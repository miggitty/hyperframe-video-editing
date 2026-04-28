---
name: how-to-edit-videos
description: Edit Marlon's talking-head videos into polished short-form ads (Facebook / Instagram / Reels) using HyperFrames — Hormozi-style word-by-word captions, motion graphics that punctuate narrative pivots, and a ghosted speaker behind full-frame graphics for continuity. Use this skill alongside the `hyperframes` skill whenever the user asks to edit, caption, subtitle, or add motion graphics to a talking-head video, especially for paid social ads (Facebook ads, Instagram ads, Reels), explainer ads, lead-gen video ads, or any video aimed at healthcare practice owners (dentists, chiropractors, podiatrists, PTs). Trigger on phrases like "make a Facebook ad from this video", "add Hormozi-style subtitles", "edit this talking-head video", "add motion graphics to this", "9:16 ad", "social ad video", or whenever the user provides a raw .mp4 of themselves talking and wants it turned into a finished ad. Use even when the user doesn't explicitly say "Hormozi" or "Facebook" — if the input is a talking-head video and the goal is a short-form ad, this skill applies.
---

# How to edit Marlon's videos

This skill captures the conventions Marlon validated through the `ad-marketing-truth` build. It runs alongside the `hyperframes` skill: hyperframes handles the framework mechanics (data attributes, GSAP, captions reference); this skill handles **the editorial style and the questions to ask before building**.

## Hard rule: never edit, trim, or cut the source video or audio

**The source video and audio run end-to-end, untouched.** This skill's job is to *add* captions and motion graphics on top — never to remove, trim, splice, fade, or shorten any part of the source. Marlon's voice is the spine of the ad; cutting any of it changes the message.

What that means concretely:

- **Composition duration must fully cover the source.** Probe with `ffprobe`, then set `data-duration` on the root composition, the `<video>`, and the `<audio>` to the **source's full duration rounded up to the next 0.5s** (e.g. source 90.566s → `data-duration="91"`). Never set duration shorter than the source.
- **`<video>` runs from `data-start="0"` for the full source duration.** No `data-end`, no trims, no clip splicing.
- **`<audio>` runs from `data-start="0"` for the full source duration with `data-volume="1"`.** Never tween audio volume. Never insert silence. Never overlay music or VO.
- **Word-level captions follow the actual transcript end-time.** If whisper's transcript extends past the source's real audio (it sometimes hallucinates a trailing word), trim the *last caption group only* so its `e` ≤ the source's audio duration. Do not edit any earlier captions. Do not retime words.
- **Motion graphic windows are additive overlays on top of the video.** They never replace, mute, or skip a portion of the source — the speaker is always playing underneath at ghost opacity.
- **No transitions that shorten the source.** No cut-to-black between sections, no jump-cuts to remove pauses, no playback-rate changes. The viewer sees the full take.

If a request would require trimming the source ("can you cut the part where I stumble", "remove the dead air at 0:42") — stop and tell Marlon that's outside the skill's scope. He should re-record or hand you a pre-trimmed source. Never make an edit decision unilaterally.

## Hard rule: never render without explicit approval

After lint + inspect pass, **start the studio editor (`npx hyperframes preview`) and stop**. Hand Marlon the localhost URL and wait for feedback. Iterate (edit → save → re-lint → he refreshes) until he says "good to render." Only then run `npx hyperframes render`. A render takes 5–10 minutes and burns the cache window — never trigger one speculatively.

## Read this first: the operating principle

Marlon's videos are direct-response ads, not corporate explainers. The voice is the spine — every editing decision serves keeping the viewer's attention on the message. Three things drive engagement:

1. **The face creates trust.** Never disappear the speaker for long stretches. When motion graphics take over, the speaker stays *ghosted* in the background at **~50–60% opacity** with a **light dim overlay (~50–60% alpha)** so the speaker is clearly visible, not a vague silhouette. Marlon validated that 22% was too dim — you couldn't see him at all. The MG copy still reads cleanly because of the contrast in font weight + stroke; you don't need to crush the video to make it work.
2. **Captions are the fallback for sound-off scrolling.** Most Facebook viewers watch muted on first scroll. Captions must be readable, on-brand, and never cover the speaker's face.
3. **Motion graphics punctuate, they don't decorate.** Each one lands on a narrative pivot (a niche reveal, a contrast, a stamp, a payoff, a CTA). If a beat doesn't have an underlying narrative reason, don't add it.

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

### MG placement decision tree

For each MG block, pick `top:` and verify the block's full height keeps `top + height` ≤ 1570. **Push every block as far down as it can go without bleeding past 1570** — face-safety is the goal, and most MG blocks Marlon has shipped could have been anchored lower than they were.

1. **Default — below center (≥ 960). The speaker's face is never covered.** Anchor at `top ≥ 960px` whenever content fits in the 610px between center and the working-band floor (1570). Works for: stat cards, single-number payoffs, stamps, chips, short stamps, CTAs with ≤ 3 bullets, 3-row lists with normal sizing. Before falling back, try one round of tightening — drop font sizes a tier (e.g. headline 110→90, bullet 38→32), reduce row gaps (22→14), trim padding — and re-measure.
2. **Below the head (top 700–900) — escape hatch when center-down truly won't fit.** Use only after the center-down attempt with tightened typography still bottoms out past 1570. Common cases: dense triplets where each row carries title + sub-result, CTA with headline + 4+ bullets + arrow, side-by-side compare cards with tall result line. Call it out in the beat-list comment so a reviewer knows it was deliberate.
3. **Over the head (top 350–500) — last resort.** Only when content genuinely can't fit even from top:700. Acceptable for very tall blocks (e.g. a 5-row list with rich rows). The safe zone is still the hard rule — `top + height` ≤ 1570 always.
4. **Never compress vertically by raising `top` past 1570 − height.** If a block bottoms out past y=1570, the fix is (a) reduce content height (smaller fonts, less padding, fewer rows) or (b) raise `top` to the next tier up — never let it bleed into the cut zone.

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

### How many beats?

**As many as the narrative justifies — no fixed count.** A 30-second ad might have 3 beats; a 90-second ad might have 6–8. Don't pad. Don't strip. Read the transcript and look for narrative pivots:

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

## Workflow (every project)

1. **Probe the source video.** `ffprobe -v error -show_entries stream=width,height,duration -of default=nw=1 source.mp4`. Confirm dimensions and duration.
2. **Scaffold a project.** `npx hyperframes init --here --no-install` inside a fresh folder, or copy the `ad-marketing-truth/my-video/` structure. Drop the source video in as `source.mp4`.
3. **Transcribe.** `npx hyperframes transcribe source.mp4 --words --out transcript.json`. Confirm word count looks right relative to duration.
4. **Build caption groups.** `python3 scripts/build_caption_groups.py transcript.json > groups.json` (script bundled with this skill).
5. **Read the full transcript.** Identify the narrative pivots → that's your MG beat list. Write the beat list as a comment in the composition before writing the HTML so the structure is clear.
6. **Write `DESIGN.md`** — short file with palette, typography, safe-zone reminder, and what-not-to-do. The `hyperframes` skill enforces this gate.
7. **Build `index.html`** — see the `ad-marketing-truth/my-video/index.html` reference. Pattern: video element + audio element + MG curtain + MG chips + captions container, all timed via `data-start` / `data-duration` / `data-track-index`.
8. **Lint, validate, inspect** in that order. `npx hyperframes lint` must be clean. `npx hyperframes validate` may produce false-positive contrast warnings for MG elements that are invisible at the validator's sample timestamps — those are safe to ignore. `npx hyperframes inspect --at <hero-frame-timestamps>` should show 0 layout issues.
9. **Open the studio editor for review — DO NOT render yet.** Marlon reviews every composition in the HyperFrames studio before render. Start the preview server in the background and give Marlon the localhost URL to open in a browser:

   ```bash
   npx hyperframes preview          # starts studio at http://localhost:5173 (default)
   ```

   Run this with `run_in_background: true` so the dev server stays up while you wait. After starting it, **stop and report**:
   - The localhost URL (read it from the preview output — port may differ if 5173 is busy)
   - A short summary of what you built (caption count, MG beat list with timestamps, any deliberate choices Marlon should sanity-check)
   - The exact prompt: *"Open the URL above in your browser, scrub through, and tell me what to change. I'll wait — no render until you sign off."*

   **Do not proceed to step 10 until Marlon explicitly approves.** Iterate on the composition (edit `index.html`, re-lint, re-inspect) — the dev server hot-reloads, so no restart needed. Each round of feedback should end with "anything else, or are we good to render?"

10. **Render into a per-source `output/` folder — only after approval.** Each source video gets its own subfolder in `output/`, named after the source file (without extension), so every deliverable stays grouped with the project that produced it.

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
11. **Verify the output** with `ffprobe`: dimensions = source dimensions, duration ≈ `data-duration` of root composition.

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

## Final delivery

Always report back with:

- Path to the rendered MP4 as a clickable markdown link
- Resolution + duration verified by `ffprobe`
- File size
- Any warnings (sparse keyframes, validation warnings) that the user should know about
- A one-paragraph summary of what was built (caption count, MG beat count, total MG duration vs speaker-only duration)

The output is a Facebook ad. The user is going to spend money pushing it to viewers. Treat the deliverable like that — verified, documented, ready to upload.
