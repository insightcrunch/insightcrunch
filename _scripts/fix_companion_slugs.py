#!/usr/bin/env python3
"""
fix_companion_slugs.py

Repoints companion-tool links whose slug does not exist on the target site to the
page that already serves the same intent.

This is the slug counterpart to fix_companion_domains.py. That script fixes the
host, this one fixes the path. Keep them separate so a bad slug rule can never
corrupt a domain rewrite.

Why this exists:
    277 posts link to reportmedic.org/tools/upsc-previous-year-question-papers.html,
    which was never built. 89 of those anchors name the PYQ Explorer explicitly,
    and upsc-pyq-explorer.html exists and serves that exact intent. Creating a
    third UPSC tool page would split authority across three competing pages, so
    the links are repointed instead.

Scope:
    _posts/*.md            article bodies and frontmatter
    _data/*.json|*.yml     link caches and manifests
    admin/*.json           dashboard data

Safe to run repeatedly. Files with no match are left untouched, so the CI commit
step produces no diff once the site is clean.

Usage:
    python _scripts/fix_companion_slugs.py --dry-run
    python _scripts/fix_companion_slugs.py
"""

import argparse
import glob
import os
import re
import sys

# Slug rewrites, applied to reportmedic.org and vaultbook.net tool paths only.
#
# Each entry: (old slug, new slug, human label)
# Add a row here whenever an audit finds a broken slug that an existing page
# already covers. Do NOT add a row for a page that genuinely needs building.
SLUG_REWRITES = [
    (
        'upsc-previous-year-question-papers.html',
        'upsc-pyq-explorer.html',
        'upsc-previous-year-question-papers -> upsc-pyq-explorer',
    ),
]

# A bare URL followed by a sentence-ending full stop, for example
#   ...find it at https://vaultbook.net/tools/film-study-notebook.html.
# Markdown autolinking swallows the stop into the path, so the link 404s.
# Wrapping the URL in angle brackets terminates it before the stop, which
# keeps the sentence punctuation intact and makes the link resolve.
BARE_URL_STOP = re.compile(
    r'(?<![(<\[])(https://(?:reportmedic\.org|vaultbook\.net)/tools/[a-z0-9-]+\.html)\.(?=\s|$)'
)

# A full stop trapped inside a markdown link target, for example
#   [text](https://.../film-study-notebook.html.)
LINKED_STOP = re.compile(
    r'\((https://(?:reportmedic\.org|vaultbook\.net)/tools/[a-z0-9-]+\.html)\.\)'
)

TARGET_GLOBS = [
    '_posts/*.md',
    '_data/*.json',
    '_data/*.yml',
    'admin/*.json',
]


def build_patterns():
    """Compile one pattern per slug rewrite, anchored to a tools path."""
    compiled = []
    for old, new, label in SLUG_REWRITES:
        pattern = re.compile(
            r'(https://(?:reportmedic\.org|vaultbook\.net)/tools/)'
            + re.escape(old)
        )
        compiled.append((pattern, r'\g<1>' + new, label))
    return compiled


def collect_files():
    files = []
    for pattern in TARGET_GLOBS:
        files.extend(glob.glob(pattern))
    return sorted(set(files))


def process(path, patterns, fix_stops, dry_run):
    """Rewrite one file. Returns a dict of label -> count, empty if unchanged."""
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            original = handle.read()
    except (UnicodeDecodeError, OSError) as exc:
        print(f"  SKIP {path}: {exc}")
        return {}

    updated = original
    counts = {}

    for pattern, replacement, label in patterns:
        updated, hits = pattern.subn(replacement, updated)
        if hits:
            counts[label] = counts.get(label, 0) + hits

    if fix_stops:
        updated, hits = LINKED_STOP.subn(r'(\g<1>)', updated)
        if hits:
            counts['full stop inside markdown link target'] = hits

        updated, hits = BARE_URL_STOP.subn(r'<\g<1>>.', updated)
        if hits:
            counts['bare URL swallowing its sentence stop'] = hits

    if not counts or updated == original:
        return {}

    if not dry_run:
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(updated)

    return counts


def main():
    parser = argparse.ArgumentParser(
        description='Repoint broken companion-tool slugs to existing pages.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Report what would change without writing any file.',
    )
    parser.add_argument(
        '--skip-stops',
        action='store_true',
        help='Leave trailing full stops inside URLs alone.',
    )
    args = parser.parse_args()

    if not os.path.isdir('_posts'):
        print('ERROR: run this from the repository root, _posts not found.')
        return 1

    patterns = build_patterns()
    files = collect_files()
    print(f"Scanning {len(files)} files for broken companion slugs.")

    changed_files = 0
    totals = {}

    for path in files:
        counts = process(path, patterns, not args.skip_stops, args.dry_run)
        if not counts:
            continue
        changed_files += 1
        for label, hits in counts.items():
            totals[label] = totals.get(label, 0) + hits

    print()
    if not totals:
        print('All companion slugs already resolve. Nothing to do.')
        return 0

    verb = 'Would rewrite' if args.dry_run else 'Rewrote'
    print(f"{verb} {sum(totals.values())} link(s) across {changed_files} file(s):")
    for label in sorted(totals):
        print(f"  {totals[label]:>6}  {label}")

    if args.dry_run:
        print('\nDry run, no files written.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
