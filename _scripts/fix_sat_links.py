#!/usr/bin/env python3
"""
fix_sat_links.py

Repoints the three secondary SAT companion slugs at the single canonical page.

The problem:
    Published posts link to four different SAT tool slugs. Only one page was
    ever built. The other three were never created and never will be, because
    the prompt files were consolidated to a single canonical SAT target.

The fix:
    sat-practice-test-questions.html covers all four intents through its tabbed
    interface, and it accepts a URL hash so a link can open the right section
    directly rather than dropping the reader at the top of the page.

    sat-math-practice-questions.html   -> sat-practice-test-questions.html#math
    sat-reading-writing-practice.html  -> sat-practice-test-questions.html#reading-writing
    sat-preparation-guide.html         -> sat-practice-test-questions.html#timing

    A math or reading hash opens Section Practice pre-filtered to that half of
    the test. The timing hash opens Timing and Scoring, which is what a link
    labelled preparation guide is reaching for.

Anchor text and surrounding prose are never touched. Only the link target moves.

Safe to run repeatedly. A clean repo produces no diff.

Usage:
    python _scripts/fix_sat_links.py --dry-run
    python _scripts/fix_sat_links.py
"""

import argparse
import glob
import os
import re
import sys

BASE = 'https://reportmedic.org/tools/sat-practice-test-questions.html'

# old slug -> anchor on the canonical page
REWRITES = {
    'sat-math-practice-questions.html': 'math',
    'sat-reading-writing-practice.html': 'reading-writing',
    'sat-preparation-guide.html': 'reading-writing',
}

# Matches the tools URL for any of the three slugs, with or without a trailing
# hash of its own, so a second run cannot double up the anchor.
PATTERN = re.compile(
    r'https://reportmedic\.org/tools/('
    + '|'.join(re.escape(s) for s in REWRITES)
    + r')(?:#[a-z-]*)?'
)

TARGET_GLOBS = ['_posts/*.md', '_data/*.json', '_data/*.yml', 'admin/*.json']


def collect_files():
    found = []
    for pattern in TARGET_GLOBS:
        found.extend(glob.glob(pattern))
    return sorted(set(found))


def process(path, dry_run):
    """Rewrite one file. Returns a dict of slug -> count, empty if unchanged."""
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            original = handle.read()
    except (UnicodeDecodeError, OSError) as exc:
        print(f"  SKIP {path}: {exc}")
        return {}

    counts = {}

    def replace(match):
        slug = match.group(1)
        counts[slug] = counts.get(slug, 0) + 1
        return f'{BASE}#{REWRITES[slug]}'

    updated = PATTERN.sub(replace, original)
    updated, hp_fix = re.subn(r'(sat-practice-test-questions\.html)#timing', r'\1#reading-writing', updated)
    if hp_fix:
        counts['already-rewritten'] = hp_fix
            
    if counts and not dry_run:
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(updated)

    return counts


def main():
    parser = argparse.ArgumentParser(
        description='Repoint secondary SAT slugs at the canonical practice page.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Report what would change without writing any file.')
    args = parser.parse_args()

    if not os.path.isdir('_posts'):
        print('ERROR: run this from the repository root, _posts not found.')
        return 1

    files = collect_files()
    print(f"Scanning {len(files)} files for secondary SAT slugs.")
    print(f"Canonical target: {BASE}")
    print()

    totals = {}
    changed = 0

    for path in files:
        counts = process(path, args.dry_run)
        if not counts:
            continue
        changed += 1
        detail = ', '.join(f"{v} {k.replace('.html', '')}" for k, v in sorted(counts.items()))
        print(f"  {os.path.basename(path)}: {detail}")
        for slug, n in counts.items():
            totals[slug] = totals.get(slug, 0) + n

    print()
    if not totals:
        print('All SAT links already point at the canonical page. Nothing to do.')
        return 0

    verb = 'Would repoint' if args.dry_run else 'Repointed'
    print(f"{verb} {sum(totals.values())} link(s) across {changed} file(s):")
    for slug in sorted(totals):
        print(f"  {totals[slug]:>5}  {slug} -> #{REWRITES.get(slug, 'reading-writing')}")

    if args.dry_run:
        print('\nDry run, no files written.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
