#!/usr/bin/env python3
"""
fix_internal_paths.py

Rewrites internal article links that use a section prefix the site does not have.

The permalink in _config.yml is /:year/:month/:day/:title/, so the only correct
internal article link is a full dated path. Several series were written against
prefixes that never existed:

    ](/blog/some-slug)       -> ](/YYYY/MM/DD/some-slug/)
    ](/insights/some-slug)   -> ](/YYYY/MM/DD/some-slug/)

The date is looked up from the matching file in _posts.

Forward links, and why the prefix is deliberately kept
------------------------------------------------------
When no post matches the slug yet, the link points at an article that has not
been written. Its future publication date is unknowable, so it cannot be
resolved now. It is left exactly as written, prefix included, on purpose.

The prefix is the marker this script uses to find the link again. Strip it to
](/slug/) and the link is still broken under a dated permalink, but now nothing
can locate it. Keeping ](/blog/slug) means that the moment the target article is
published, the next run of this script resolves it automatically.

That is why this script belongs in the Jekyll workflow alongside the other
per-build scripts, not as a one-off cleanup. Run once, it fixes today's backlog.
Run on every build, forward links heal themselves on the day their target goes
live and no link is ever broken after publication.

--strip-unwritten exists for a one-time audit only. It removes the marker, so
those links can never be auto-resolved afterwards. Do not use it in CI.

The /reportmedic/ prefix is deliberately NOT handled here. Those links point at
a section of insightcrunch.com that was never built, and there is no correct
target to rewrite to. They need a human decision: unlink the prose, or repoint
each one at a real reportmedic.org tool page. The script reports them and stops.

Safe to run repeatedly. A clean repo produces no diff.

Usage:
    python _scripts/fix_internal_paths.py --dry-run
    python _scripts/fix_internal_paths.py
    python _scripts/fix_internal_paths.py --strip-unwritten
"""

import argparse
import glob
import os
import re
import sys

PREFIXES = ['blog', 'insights']

# ](/prefix/slug) or ](/prefix/slug/) , with or without a trailing slash.
LINK = re.compile(r'\]\(/(' + '|'.join(PREFIXES) + r')/([a-z0-9][a-z0-9-]*)/?\)')

# Reported, never rewritten. No valid target exists.
ORPHAN = re.compile(r'\]\(/reportmedic/([a-z0-9][a-z0-9-]*)/?\)')

POST_NAME = re.compile(r'^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$')


def build_index():
    """Map every post slug to its published date parts."""
    index = {}
    for path in glob.glob('_posts/*.md'):
        match = POST_NAME.match(os.path.basename(path))
        if match:
            index[match.group(4)] = (match.group(1), match.group(2), match.group(3))
    return index


def process(path, index, strip_unwritten, dry_run):
    """Rewrite one file. Returns (counts dict, orphan slug list)."""
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            original = handle.read()
    except (UnicodeDecodeError, OSError) as exc:
        print(f"  SKIP {path}: {exc}")
        return {}, []

    counts = {'resolved': 0, 'stripped': 0, 'left': 0}

    def replace(match):
        slug = match.group(2)
        if slug in index:
            year, month, day = index[slug]
            counts['resolved'] += 1
            return f']( /{year}/{month}/{day}/{slug}/)'.replace('( /', '(/')
        if strip_unwritten:
            counts['stripped'] += 1
            return f']( /{slug}/)'.replace('( /', '(/')
        counts['left'] += 1
        return match.group(0)

    updated = LINK.sub(replace, original)
    orphans = ORPHAN.findall(original)

    if updated != original and not dry_run:
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(updated)

    if not any(counts.values()):
        counts = {}

    return counts, orphans


def main():
    parser = argparse.ArgumentParser(
        description='Rewrite prefixed internal links to full dated permalinks.'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Report what would change without writing any file.')
    parser.add_argument('--strip-unwritten', action='store_true',
                        help='One-time audit only. Drops the prefix from links to unwritten '
                             'posts, which removes the marker this script needs to resolve '
                             'them later. Never use this in CI.')
    args = parser.parse_args()

    if not os.path.isdir('_posts'):
        print('ERROR: run this from the repository root, _posts not found.')
        return 1

    index = build_index()
    files = sorted(glob.glob('_posts/*.md'))
    print(f"Indexed {len(index)} published posts.")
    print(f"Scanning {len(files)} files for prefixed internal links.")
    print()

    totals = {'resolved': 0, 'stripped': 0, 'left': 0}
    changed_files = 0
    orphan_files = 0
    orphan_links = 0

    for path in files:
        counts, orphans = process(path, index, args.strip_unwritten, args.dry_run)
        if orphans:
            orphan_files += 1
            orphan_links += len(orphans)
        if not counts:
            continue
        if counts.get('resolved') or counts.get('stripped'):
            changed_files += 1
        for key in totals:
            totals[key] += counts.get(key, 0)

    verb = 'Would rewrite' if args.dry_run else 'Rewrote'
    print(f"{verb} {totals['resolved']} link(s) to full dated permalinks "
          f"across {changed_files} file(s).")
    if totals['stripped']:
        print(f"  Stripped the prefix from {totals['stripped']} forward link(s) "
              f"to unwritten posts.")
    if totals['left']:
        print(f"  Left {totals['left']} forward link(s) to unwritten posts untouched, "
              f"prefix intact.")
        print("  These resolve automatically on the first run after their target is")
        print("  published. Keep this script in the Jekyll workflow and they heal")
        print("  themselves. Do not strip the prefix, it is the marker.")

    if orphan_links:
        print()
        print(f"NOT FIXED: {orphan_links} link(s) to /reportmedic/ across "
              f"{orphan_files} file(s).")
        print("  That section does not exist on this site and no correct target can be")
        print("  inferred. Either unlink the prose or repoint each link at a real")
        print("  reportmedic.org tool page. This needs a human decision per link.")

    if args.dry_run:
        print('\nDry run, no files written.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
