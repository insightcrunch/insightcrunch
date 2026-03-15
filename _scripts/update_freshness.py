#!/usr/bin/env python3
"""
update_freshness.py
===================
Pre-build script for InsightCrunch.

Picks a batch of posts that haven't been refreshed in the longest time,
updates their `last_updated` front-matter field to today's date, and
writes back the manifest so the next run picks the next-stalest batch.

Usage:  python _scripts/update_freshness.py [--batch-size 15] [--posts-dir _posts] [--manifest _data/freshness_manifest.json]
"""

import argparse
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

# ── config defaults ──────────────────────────────────────────────
DEFAULT_BATCH = 15
DEFAULT_POSTS = "_posts"
DEFAULT_MANIFEST = "_data/freshness_manifest.json"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LAST_UPDATED_RE = re.compile(r"^last_updated:\s*.*$", re.MULTILINE)


def load_manifest(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def get_all_posts(posts_dir: Path) -> list[Path]:
    return sorted(posts_dir.glob("*.md"))


def pick_batch(posts: list[Path], manifest: dict, batch_size: int) -> list[Path]:
    """Return the `batch_size` posts with the oldest (or missing) manifest entry."""
    def sort_key(p):
        entry = manifest.get(p.name)
        if entry is None:
            return "0000-00-00"          # never touched = highest priority
        return entry.get("last_refreshed", "0000-00-00")

    ranked = sorted(posts, key=sort_key)
    return ranked[:batch_size]


def update_front_matter(filepath: Path, today_str: str) -> bool:
    """Inject or replace `last_updated` in the YAML front matter. Returns True if changed."""
    text = filepath.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return False  # no front matter found, skip

    fm_block = m.group(1)

    if LAST_UPDATED_RE.search(fm_block):
        new_fm = LAST_UPDATED_RE.sub(f"last_updated: {today_str}", fm_block)
    else:
        new_fm = fm_block.rstrip() + f"\nlast_updated: {today_str}"

    if new_fm == fm_block:
        return False  # already set to today

    new_text = f"---\n{new_fm}\n---\n" + text[m.end():]
    filepath.write_text(new_text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Refresh last_updated on a rolling batch of posts.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    parser.add_argument("--posts-dir", type=str, default=DEFAULT_POSTS)
    parser.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    posts_dir = Path(args.posts_dir)
    manifest_path = Path(args.manifest)
    today_str = date.today().isoformat()

    manifest = load_manifest(manifest_path)
    all_posts = get_all_posts(posts_dir)
    batch = pick_batch(all_posts, manifest, args.batch_size)

    changed = 0
    for post_path in batch:
        if update_front_matter(post_path, today_str):
            changed += 1
        manifest[post_path.name] = {
            "last_refreshed": today_str
        }

    save_manifest(manifest_path, manifest)

    total = len(all_posts)
    cycle_days = (total / args.batch_size) * 4  # rebuilds every 4 days
    print(f"[freshness] {changed}/{len(batch)} posts updated (last_updated -> {today_str})")
    print(f"[freshness] {total} total posts, batch {args.batch_size}, full cycle ~ {cycle_days:.0f} days")


if __name__ == "__main__":
    main()
