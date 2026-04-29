#!/usr/bin/env python3
"""
Generate full-frame story images for a HyperFrames video edit via kie.ai gpt-image-2.

Input:  image-plan.json — array of { id, start, duration, prompt, style?, type? }
        (the structured form of the markdown table Marlon approved in chat)
Output: images/{id}.png for each row, plus images/manifest.json

Rules:
- Source video aspect ratio is auto-detected with ffprobe and mapped to a kie.ai value
  (9:16, 1:1, 16:9, 3:4, 4:3). Resolution is always 1K.
- API key read from project-local .env (KIE_API_KEY=...).
- Idempotent: skips rows whose PNG already exists unless --force.
- NEVER touches source.mp4, transcript.json, or the composition.

Usage:
    python3 generate_images.py image-plan.json --source source.mp4
    python3 generate_images.py image-plan.json --source source.mp4 --force
    python3 generate_images.py image-plan.json --source source.mp4 --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://api.kie.ai/api/v1/jobs"
MODEL = "gpt-image-2-text-to-image"
POLL_INTERVAL = 4
POLL_TIMEOUT = 300


def load_env(project_root: Path) -> None:
    env = project_root / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def detect_aspect_ratio(source: Path) -> str:
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x", str(source),
    ], text=True).strip()
    w_str, h_str = out.split("x")[:2]
    w, h = int(w_str), int(h_str)
    ratio = w / h
    candidates = {
        "9:16": 9 / 16,
        "3:4":  3 / 4,
        "1:1":  1.0,
        "4:3":  4 / 3,
        "16:9": 16 / 9,
    }
    best = min(candidates.items(), key=lambda kv: abs(kv[1] - ratio))
    return best[0]


def post_json(url: str, body: dict, key: str) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def get_json(url: str, key: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def create_task(prompt: str, aspect_ratio: str, key: str) -> str:
    body = {
        "model": MODEL,
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": "1K",
        },
    }
    res = post_json(f"{API_BASE}/createTask", body, key)
    if res.get("code") != 200:
        raise RuntimeError(f"createTask failed: {res}")
    task_id = res["data"]["taskId"]
    return task_id


def poll_task(task_id: str, key: str) -> str:
    deadline = time.time() + POLL_TIMEOUT
    url = f"{API_BASE}/recordInfo?taskId={task_id}"
    while time.time() < deadline:
        try:
            res = get_json(url, key)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(POLL_INTERVAL)
                continue
            raise
        data = res.get("data") or {}
        state = data.get("state") or data.get("status")
        if state in ("success", "completed", "SUCCESS"):
            rj = data.get("resultJson")
            if isinstance(rj, str):
                try:
                    rj = json.loads(rj)
                except Exception:
                    rj = {}
            rj = rj or {}
            info = data.get("info")
            if isinstance(info, str):
                try:
                    info = json.loads(info)
                except Exception:
                    info = {}
            info = info or {}
            urls = (
                rj.get("result_urls")
                or rj.get("resultUrls")
                or info.get("result_urls")
                or data.get("result_urls")
            )
            if urls:
                return urls[0]
        if state in ("fail", "failed", "FAIL"):
            raise RuntimeError(f"task {task_id} failed: {res}")
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"task {task_id} did not finish within {POLL_TIMEOUT}s")


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", type=Path, help="image-plan.json")
    ap.add_argument("--source", type=Path, required=True, help="source.mp4")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("images"))
    args = ap.parse_args()

    project_root = args.plan.parent.resolve()
    load_env(project_root)

    if not args.source.exists():
        print(f"source not found: {args.source}", file=sys.stderr)
        return 2

    aspect = detect_aspect_ratio(args.source)
    print(f"[info] source aspect → {aspect}")

    plan = json.loads(args.plan.read_text())
    if not isinstance(plan, list):
        print("plan must be a JSON array", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        for row in plan:
            print(f"[dry] {row['id']:>16}  start={row['start']}  dur={row['duration']}  prompt={row['prompt'][:80]}…")
        return 0

    key = os.environ.get("KIE_API_KEY")
    if not key:
        print("KIE_API_KEY missing — set it in .env or env", file=sys.stderr)
        return 2

    manifest = []
    for row in plan:
        rid = row["id"]
        png = args.out / f"{rid}.png"
        if png.exists() and not args.force:
            print(f"[skip] {rid} (exists)")
            manifest.append({**{k: row[k] for k in ("id", "start", "duration")}, "file": str(png), "prompt": row["prompt"]})
            continue
        print(f"[gen]  {rid} …")
        task_id = create_task(row["prompt"], aspect, key)
        url = poll_task(task_id, key)
        download(url, png)
        print(f"       → {png}")
        manifest.append({**{k: row[k] for k in ("id", "start", "duration")}, "file": str(png), "prompt": row["prompt"]})

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[done] {len(manifest)} images, manifest at {args.out/'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
