#!/usr/bin/env python3
"""
Build Hormozi-style caption groups from a HyperFrames word-level transcript.

Input:  a transcript.json file (array of { text, start, end } objects, as produced by
        `npx hyperframes transcribe --words`)
Output: groups.json on stdout — array of caption groups ready to embed in a HyperFrames
        composition, where each group is { s, e, w: [{ t, s, e }, ...] }.

Rules (validated by Marlon's ad-marketing-truth build):
- 3 words per group max — high-energy Hormozi pacing
- Break on terminal punctuation (. ? !), comma after 2+ words, or pauses ≥ 300ms
- Extend each group's `e` to just before the next group's `s` so captions stay through
  micro-gaps (no flicker), with a 250ms cap so they don't linger past the spoken word
- Final group gets a 300ms tail

Usage:
    python3 build_caption_groups.py transcript.json > groups.json
    python3 build_caption_groups.py transcript.json -o groups.json
"""

import argparse
import json
import sys


def build_groups(words, max_words=3, pause_break=0.30, tail_extend=0.25, final_tail=0.30):
    groups = []
    cur = []

    def flush():
        if not cur:
            return
        groups.append({
            "s": cur[0]["start"],
            "e": cur[-1]["end"],
            "w": [{"t": w["text"], "s": w["start"], "e": w["end"]} for w in cur],
        })
        cur.clear()

    for i, w in enumerate(words):
        cur.append(w)
        text = w["text"]
        is_terminal = text.endswith((".", "?", "!"))
        is_comma = text.endswith(",")
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = (nxt["start"] - w["end"]) if nxt else 99

        if (
            is_terminal
            or pause >= pause_break
            or len(cur) >= max_words
            or (is_comma and len(cur) >= 2)
        ):
            flush()

    flush()

    # Extend each group's `e` toward the next group's `s` (capped) so captions don't
    # flicker through micro-gaps, but never linger past the spoken word.
    for i, g in enumerate(groups):
        if i + 1 < len(groups):
            g["e"] = min(groups[i + 1]["s"], g["e"] + tail_extend)
        else:
            g["e"] = g["e"] + final_tail

    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1] if __doc__ else None)
    parser.add_argument("transcript", help="Path to transcript.json (word-level)")
    parser.add_argument(
        "-o",
        "--output",
        help="Output path (defaults to stdout)",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=3,
        help="Max words per caption group (default: 3)",
    )
    parser.add_argument(
        "--pause-break",
        type=float,
        default=0.30,
        help="Pause threshold (seconds) that forces a group break (default: 0.30)",
    )
    args = parser.parse_args()

    with open(args.transcript) as f:
        words = json.load(f)

    if not isinstance(words, list) or not words:
        print("error: transcript must be a non-empty array of word objects", file=sys.stderr)
        sys.exit(1)
    if "text" not in words[0] or "start" not in words[0] or "end" not in words[0]:
        print(
            "error: transcript words must have 'text', 'start', 'end' fields",
            file=sys.stderr,
        )
        sys.exit(1)

    groups = build_groups(words, max_words=args.max_words, pause_break=args.pause_break)

    out = json.dumps(groups)
    if args.output:
        with open(args.output, "w") as f:
            f.write(out)
        print(f"wrote {len(groups)} groups to {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
