# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this workspace is

A HyperFrames-based pipeline for turning Marlon's raw talking-head footage (in `raw-videos/`) into polished short-form social ads (Facebook / Instagram / Reels) at 9:16. Each ad is its own `projects/ad-N-*/my-video/` HyperFrames composition. The output is a 1080×1920 MP4 with Hormozi-style word-by-word captions, motion-graphic punctuation beats, and AI-generated infographic cutaways.

## Workspace layout

- `raw-videos/` — immutable source `.mp4` files. **Never trim, splice, or alter these.**
- `projects/ad-N-*/my-video/` — one HyperFrames project per ad. Contains:
  - `index.html` — the composition (root timeline, captions, MGs, cutaways, GSAP)
  - `source.mp4` — the immutable source for this ad
  - `transcript.json` — whisper word-level timings (used to anchor captions and visual beats)
  - `image-plan.json` — kie.ai cutaway prompts + start/duration
  - `images/` — generated cutaway PNGs (idempotent; only `--force` re-fetches)
  - `renders/` — final MP4 outputs (named e.g. `Ad 1 - The New Opportunity.mp4`)
- `.claude/skills/` — installed HyperFrames skills + the custom `how-to-edit-videos` skill that encodes the editorial style

## Critical: invoke the `how-to-edit-videos` skill before ANY ad-editing work

The skill (`.claude/skills/how-to-edit-videos/SKILL.md`) encodes Marlon-validated rules that are NOT discoverable from the code: tiered cutaway hold times, punchline-coverage anchoring, MG safe-zone (`top ≥ 960`), Hormozi-style caption layout, the 4:5 Facebook crop safe zone, beat budget caps. Skipping it produces ads that get rejected on review. Read the skill once with `limit: 200`, then reference targeted sections.

The HyperFrames framework rules (data attributes, GSAP timeline registration, etc.) live in the `hyperframes` skill — invoke that for framework mechanics.

## Commands

Run from inside the project's `my-video/` directory:

```bash
npx hyperframes lint                  # validate composition (must be 0 errors before preview)
npx hyperframes preview               # studio editor at http://localhost:3002 (auto-picks port if 3002 taken)
npx hyperframes preview --force-new   # start a fresh server instead of reusing existing
npx hyperframes render                # produce MP4 in renders/ (5–10 min per ad)
npx hyperframes inspect --at <times>  # screenshot at specific timestamps (catches safe-zone violations)
npx hyperframes transcribe --words    # whisper transcript with word-level timings
npx hyperframes docs <topic>          # offline reference: data-attributes, gsap, compositions, rendering, examples, troubleshooting
```

To render all 5 ads sequentially (parallel risks Chrome compositor starvation), use a chained shell loop with `nohup` so it survives.

To verify dimensions and source duration before editing:

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 source.mp4
```

## Hard rules (operational, not editorial)

1. **Never edit, trim, or splice the source video/audio.** The source has already been edited; pauses are deliberate. Composition `data-duration` ≥ source duration on the root, `<video>`, and `<audio>` (round up to next 0.5s). `<video>` and `<audio>` always run from `data-start="0"` for the full source duration.
2. **Never render without explicit user approval.** A render takes 5–10 min and burns the cache window. Always `preview` first, hand the localhost URL to the user, wait for "good to render."
3. **Render dimensions must match source dimensions** (probe with `ffprobe`; never hard-code).
4. **Don't regenerate kie.ai images on every iteration.** The `generate_images.py` script is idempotent — only `--force` re-fetches existing PNGs (each one costs API credit).

## Persistent feedback memory

User-specific feedback rules accumulate at `~/.claude/projects/-Users-marlonmarescia-Documents-GitHub-MARKETING-hyperframe-Video-Editing/memory/`. The `MEMORY.md` index there is auto-loaded into every session — check it first for project-specific conventions Marlon has validated (e.g. cutaway hold tiers, punchline-coverage rule, MG head-clearance, caption container layout). When user feedback yields a new convention, save it as `feedback_*.md` and add an index line.

## Model recommendation

Use Claude Sonnet 4.6 (`claude-sonnet-4-6`) for ad editing — the workflow is highly prescriptive (no open-ended reasoning needed) and Sonnet is ~5× cheaper than Opus at no quality cost. The repo defaults to Sonnet via `.claude/settings.json`. Reserve Opus for genuine off-playbook work (new ad genres, debugging unfamiliar edge cases).

## Token-efficiency reminders

- `transcript.json` is ~1200 lines per minute of source — never `Read` end-to-end. Use `python3 -c` or `jq` to slice.
- The 93+ caption groups embedded in each `index.html` make the file long. Read targeted line ranges, not the whole file.
- Use the `Explore` sub-agent for codebase searches that span multiple files.
