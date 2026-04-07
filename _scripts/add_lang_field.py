#!/usr/bin/env python3
"""
add_lang_field.py

Walks _posts/ and adds a `lang:` field to the YAML frontmatter of any post
that doesn't already have one.

Detection logic:
  1. Read page_title if present, otherwise fall back to title.
  2. Pass 1: if the chosen title is purely in ONE script (no mixture),
     use that script's language code.
  3. Pass 2: if the title has any mixture of scripts (or is empty),
     use body-majority. Whichever script has the most characters in
     the body wins. If the body has fewer script chars than the title,
     fall back to the dominant script in the title.

Idempotent: re-running does nothing on posts that already have `lang:`.
First run on CI will backfill all existing posts in a single commit.
"""

import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"

LANG_RANGES = [
    ("en", re.compile(r"[A-Za-z]")),                       # Latin (English)
    ("zh", re.compile(r"[\u4E00-\u9FFF\u3400-\u4DBF]")),   # CJK Unified
    ("bn", re.compile(r"[\u0980-\u09FF]")),                # Bengali
    ("hi", re.compile(r"[\u0900-\u097F]")),                # Devanagari (Hindi)
    ("ta", re.compile(r"[\u0B80-\u0BFF]")),                # Tamil
    ("te", re.compile(r"[\u0C00-\u0C7F]")),                # Telugu
    ("kn", re.compile(r"[\u0C80-\u0CFF]")),                # Kannada
    ("ml", re.compile(r"[\u0D00-\u0D7F]")),                # Malayalam
    ("ur", re.compile(r"[\u0600-\u06FF]")),                # Arabic script (Urdu)
]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)
TITLE_RE       = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.MULTILINE)
PAGE_TITLE_RE  = re.compile(r'^page_title:\s*"?(.*?)"?\s*$', re.MULTILINE)
LANG_RE        = re.compile(r'^lang:\s*\S+\s*$', re.MULTILINE)


def _count_scripts(text: str) -> dict:
    return {code: len(rx.findall(text)) for code, rx in LANG_RANGES}


def detect_lang(title: str, body: str) -> str:
    title_counts = _count_scripts(title)
    nonzero_in_title = [code for code, n in title_counts.items() if n > 0]

    # Pass 1: pure title (exactly one script present)
    if len(nonzero_in_title) == 1:
        return nonzero_in_title[0]

    # Pass 2: mixed or empty title -> body majority with title fallback
    body_counts = _count_scripts(body)
    body_total = sum(body_counts.values())
    title_total = sum(title_counts.values())

    if body_total < title_total:
        winner = max(title_counts.items(), key=lambda x: x[1])
        return winner[0] if winner[1] > 0 else "en"

    if body_total == 0:
        return "en"

    return max(body_counts.items(), key=lambda x: x[1])[0]


def process_file(path: Path) -> str:
    """Returns 'skipped', 'added:<lang>', or 'no-frontmatter'."""
    raw = path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(raw)
    if not fm_match:
        return "no-frontmatter"

    frontmatter = fm_match.group(1)
    body = raw[fm_match.end():]

    if LANG_RE.search(frontmatter):
        return "skipped"

    # Prefer page_title (richer, SEO-optimized). Fall back to title if absent.
    page_title_match = PAGE_TITLE_RE.search(frontmatter)
    title_match      = TITLE_RE.search(frontmatter)
    if page_title_match:
        title_for_detection = page_title_match.group(1)
    elif title_match:
        title_for_detection = title_match.group(1)
    else:
        title_for_detection = ""

    lang = detect_lang(title_for_detection, body)

    new_frontmatter = frontmatter.rstrip() + f"\nlang: {lang}\n"
    new_raw = f"---\n{new_frontmatter}---\n" + body
    path.write_text(new_raw, encoding="utf-8")
    return f"added:{lang}"


def main() -> int:
    if not POSTS_DIR.is_dir():
        print(f"ERROR: {POSTS_DIR} not found", file=sys.stderr)
        return 1

    counts = {
        "skipped": 0, "no-frontmatter": 0,
        "added:en": 0, "added:zh": 0, "added:bn": 0,
        "added:hi": 0, "added:ta": 0, "added:te": 0,
        "added:kn": 0, "added:ml": 0, "added:ur": 0,
    }
    for md in sorted(POSTS_DIR.glob("*.md")):
        result = process_file(md)
        counts[result] = counts.get(result, 0) + 1

    print("Language tagging complete:")
    for k, v in counts.items():
        print(f"  {k:18s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
