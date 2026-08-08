#!/usr/bin/env python3
"""
fix_companion_domains.py

Rewrites companion-tool links to their canonical hosts across the site.

Owned domains:
    insightcrunch.com
    vaultbook.net
    reportmedic.org

VaultBook links were written against vaultbook.org in several series prompt files.
That domain is not owned. This script rewrites every occurrence to vaultbook.net.

Scope:
    _posts/*.md            article bodies and frontmatter
    _data/*.json|*.yml     link caches and manifests
    admin/*.json           dashboard data

Safe to run repeatedly. Files with no match are left untouched, so the CI commit
step produces no diff once the site is clean.

Usage:
    python _scripts/fix_companion_domains.py
    python _scripts/fix_companion_domains.py --dry-run
"""

import argparse
import glob
import os
import re
import sys

# Canonical rewrites. Add a row here if another domain ever drifts.
# Each entry: (compiled pattern, replacement, human label)
REWRITES = [
    (re.compile(r'\bvaultbook\.org\b'), 'vaultbook.net', 'vaultbook.org -> vaultbook.net'),
    (re.compile(r'\bwww\.vaultbook\.org\b'), 'vaultbook.net', 'www.vaultbook.org -> vaultbook.net'),
    (re.compile(r'\bwww\.vaultbook\.net\b'), 'vaultbook.net', 'strip www from vaultbook.net'),
    (re.compile(r'\breportmedic\.com\b'), 'reportmedic.org', 'reportmedic.com -> reportmedic.org'),
    (re.compile(r'\bwww\.reportmedic\.org\b'), 'reportmedic.org', 'strip www from reportmedic.org'),
]

TARGET_GLOBS = [
    '_posts/*.md',
    '_data/*.json',
    '_data/*.yml',
    'admin/*.json',
]


def collect_files():
    files = []
    for pattern in TARGET_GLOBS:
        files.extend(glob.glob(pattern))
    return sorted(set(files))


def process(path, dry_run):
    """Rewrite one file. Returns a dict of label -> count, empty if unchanged."""
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            original = handle.read()
    except (UnicodeDecodeError, OSError) as exc:
        print(f"  SKIP {path}: {exc}")
        return {}

    updated = original
    counts = {}

    for pattern, replacement, label in REWRITES:
        updated, hits = pattern.subn(replacement, updated)
        if hits:
            counts[label] = counts.get(label, 0) + hits

    if not counts or updated == original:
        return {}

    if not dry_run:
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(updated)

    return counts


def main():
    parser = argparse.ArgumentParser(
        description='Rewrite companion-tool links to canonical owned domains.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Report what would change without writing any file.',
    )
    args = parser.parse_args()

    if not os.path.isdir('_posts'):
        print('ERROR: run this from the repository root, _posts not found.')
        return 1

    files = collect_files()
    print(f"Scanning {len(files)} files for non-canonical companion domains.")

    changed_files = 0
    totals = {}

    for path in files:
        counts = process(path, args.dry_run)
        if not counts:
            continue
        changed_files += 1
        for label, hits in counts.items():
            totals[label] = totals.get(label, 0) + hits

    print()
    if not totals:
        print('All companion links already canonical. Nothing to do.')
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
