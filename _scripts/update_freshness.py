#!/usr/bin/env python3
"""
update_freshness.py
===================
Pre-build script for InsightCrunch.

Picks a batch of posts that haven't been refreshed in the longest time,
updates their `last_updated` front-matter field to today's date,
rotates their meta description (excerpt) from meta_variants.json,
and writes back the manifest so the next run picks the next-stalest batch.

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
DEFAULT_META_VARIANTS = "_data/meta_variants.json"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LAST_UPDATED_RE = re.compile(r"^last_updated:\s*.*$", re.MULTILINE)
EXCERPT_RE = re.compile(r'^(excerpt:\s*["\x27])(.*?)(["\x27]\s*)$', re.MULTILINE)


def load_json(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict, ensure_ascii=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=ensure_ascii)


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


def update_front_matter(filepath: Path, today_str: str, new_excerpt: str = None) -> bool:
    """Inject or replace `last_updated` and optionally `excerpt` in YAML front matter."""
    text = filepath.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return False

    fm_block = m.group(1)
    changed = False

    # ── Update last_updated ──
    if LAST_UPDATED_RE.search(fm_block):
        new_fm = LAST_UPDATED_RE.sub(f"last_updated: {today_str}", fm_block)
    else:
        new_fm = fm_block.rstrip() + f"\nlast_updated: {today_str}"

    if new_fm != fm_block:
        changed = True
        fm_block = new_fm

    # ── Rotate excerpt if a new one is provided ──
    if new_excerpt:
        # Escape any quotes in the new excerpt to avoid breaking YAML
        safe_excerpt = new_excerpt.replace('"', '\\"')
        excerpt_match = EXCERPT_RE.search(fm_block)
        if excerpt_match:
            old_excerpt = excerpt_match.group(2)
            if old_excerpt != safe_excerpt:
                # Preserve the original quote style (single or double)
                quote_char = excerpt_match.group(1)[-1]
                if quote_char == "'":
                    safe_excerpt = new_excerpt.replace("'", "\\'")
                new_line = f'{excerpt_match.group(1)}{safe_excerpt}{excerpt_match.group(3)}'
                fm_block = fm_block[:excerpt_match.start()] + new_line + fm_block[excerpt_match.end():]
                changed = True

    if not changed:
        return False

    new_text = f"---\n{fm_block}\n---\n" + text[m.end():]
    filepath.write_text(new_text, encoding="utf-8")
    return True


def get_next_excerpt(meta_variants: dict, filename: str) -> str | None:
    """Rotate to next variant and return the new excerpt text, or None if not in variants."""
    entry = meta_variants.get(filename)
    if not entry:
        return None

    # Rotate: 0 -> 1 -> 2 -> 0
    current = entry.get("current", 0)
    next_idx = (current + 1) % 3

    variant_keys = ["original", "variant_1", "variant_2"]
    new_excerpt = entry.get(variant_keys[next_idx], "")

    # Skip rotation if all variants are the same (placeholder posts)
    if entry.get("variant_1") == entry.get("original") and entry.get("variant_2") == entry.get("original"):
        return None

    # Update the current index
    entry["current"] = next_idx
    return new_excerpt if new_excerpt else None


def main():
    parser = argparse.ArgumentParser(description="Refresh last_updated and rotate meta descriptions.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    parser.add_argument("--posts-dir", type=str, default=DEFAULT_POSTS)
    parser.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST)
    parser.add_argument("--meta-variants", type=str, default=DEFAULT_META_VARIANTS)
    args = parser.parse_args()

    posts_dir = Path(args.posts_dir)
    manifest_path = Path(args.manifest)
    meta_path = Path(args.meta_variants)
    today_str = date.today().isoformat()

    manifest = load_json(manifest_path)
    meta_variants = load_json(meta_path)
    all_posts = get_all_posts(posts_dir)
    batch = pick_batch(all_posts, manifest, args.batch_size)

    changed = 0
    rotated = 0
    for post_path in batch:
        # Get next meta description variant (if available)
        new_excerpt = get_next_excerpt(meta_variants, post_path.name)
        if new_excerpt:
            rotated += 1

        if update_front_matter(post_path, today_str, new_excerpt):
            changed += 1

        manifest[post_path.name] = {
            "last_refreshed": today_str
        }

    save_json(manifest_path, manifest)
    save_json(meta_path, meta_variants, ensure_ascii=False)

    total = len(all_posts)
    cycle_days = (total / args.batch_size) * 4  # rebuilds every 4 days
    print(f"[freshness] {changed}/{len(batch)} posts updated (last_updated -> {today_str})")
    print(f"[freshness] {rotated}/{len(batch)} meta descriptions rotated")
    print(f"[freshness] {total} total posts, batch {args.batch_size}, full cycle ~ {cycle_days:.0f} days")


if __name__ == "__main__":
    main()
