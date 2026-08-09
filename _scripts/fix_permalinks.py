#!/usr/bin/env python3
"""
fix_permalinks.py

ONE-TIME repair. Not part of the build.

_config.yml sets:

    permalink: /:year/:month/:day/:title/

There is no jekyll-redirect-from plugin and no redirect_from entry anywhere, so
the dated path is the only URL that serves a post. Legacy articles written
before that rule was locked contain five broken link shapes. This script
normalises all five.

    A  flat path                 ](/some-slug/)                -> ](/YYYY/MM/DD/some-slug/)
    B  right slug, wrong date    ](/2023/05/13/some-slug/)     -> ](/2023/05/21/some-slug/)
    C  section prefix            ](/blog/some-slug)            -> ](/YYYY/MM/DD/some-slug/)
    D  filename pasted in link   ](/2008-02-26-some-slug)      -> ](/2008/02/26/some-slug/)
    E  no leading slash          ](some-slug)                  -> ](/YYYY/MM/DD/some-slug/)

The date always comes from the target's own filename in _posts. Nothing is
guessed.

A link whose slug has no matching file is LEFT EXACTLY AS WRITTEN. Those point
at articles not yet published. Their dates come from the locked slug and date
tables and match the filename the article will eventually carry, so they start
working on publication day without any further action.

Anchor text is never modified. Only the target inside the parentheses changes.

Code fences, tilde fences and inline backticks are blanked before scanning, so
code samples such as [int]($_.WorkingSet64/1MB) are never touched.

Usage:
    python3 _scripts/fix_permalinks.py            dry run, prints what it would do
    python3 _scripts/fix_permalinks.py --apply    writes the files

Idempotent. A second run reports nothing to change.
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict

POSTS_DIR = "_posts"

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$")
DATED_RE = re.compile(r"^/(\d{4})/(\d{2})/(\d{2})/([^/]+)/?$")
DATE_PREFIX_RE = re.compile(r"^/?(\d{4})-(\d{2})-(\d{2})-(.+?)/?$")

# Section prefixes that were written into prose but never existed on the site.
KNOWN_PREFIXES = ("blog", "a-levels", "posts", "sat", "articles",
                  "insights", "us-presidents")

# Markdown inline link, target captured. Allows one level of nested brackets in
# the anchor text.
LINK_RE = re.compile(r"\[(?:[^\]\[]|\[[^\]]*\])*\]\(([^)\s]+)(\s+\"[^\"]*\")?\)")

# Raw HTML anchors also appear in some posts and need the same treatment.
HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']")

SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "//", "#")


def build_slug_index(posts_dir):
    """slug -> sorted list of (yyyy, mm, dd). A slug used by more than one file
    is a duplicate post. Both of its URLs are valid, so a dated link to either
    is correct, but an undated link cannot be resolved without a human."""
    seen = defaultdict(set)
    for name in os.listdir(posts_dir):
        m = FILENAME_RE.match(name)
        if m:
            seen[m.group(4)].add((m.group(1), m.group(2), m.group(3)))
    index = {slug: sorted(dates) for slug, dates in seen.items()}
    duplicates = sorted(s for s, d in index.items() if len(d) > 1)
    return index, duplicates


def blank(match):
    """Same length, same newlines, no content. Offsets must stay identical to
    the real body or the safety check in process() rejects valid edits."""
    return "".join("\n" if c == "\n" else " " for c in match.group(0))


def mask_code(body):
    """Blank code regions so link scanning never sees them. Length and newline
    positions are preserved exactly."""
    body = re.sub(r"```.*?```", blank, body, flags=re.S)
    body = re.sub(r"~~~.*?~~~", blank, body, flags=re.S)
    body = re.sub(r"`[^`\n]*`", blank, body)
    return body


def dated(slug, date):
    return "/%s/%s/%s/%s/" % (date[0], date[1], date[2], slug)


def resolve(slug, index, frag, tag):
    dates = index.get(slug)
    if not dates:
        return None, "unpublished"
    if len(dates) > 1:
        return None, "duplicate"
    return dated(slug, dates[0]) + frag, tag


def classify(target, index):
    """Return (new_target, pattern_letter) or (None, reason) if untouched."""
    base = target.split("#", 1)[0].split("?", 1)[0]
    frag = target[len(base):]

    if base.startswith(SKIP_SCHEMES) or base == "/" or base == "":
        return None, "skip"

    # D: whole filename pasted as the link, with or without a leading slash
    m = DATE_PREFIX_RE.match(base)
    if m and "/" not in base.strip("/"):
        return resolve(m.group(4), index, frag, "D")

    # B: already dated, verify the date against the filename
    m = DATED_RE.match(base)
    if m:
        slug = m.group(4)
        dates = index.get(slug)
        if not dates:
            return None, "unpublished"
        if (m.group(1), m.group(2), m.group(3)) in dates:
            return None, "already correct"
        if len(dates) > 1:
            return None, "duplicate"
        return dated(slug, dates[0]) + frag, "B"

    if base.startswith("/"):
        segments = [s for s in base.strip("/").split("/") if s]
        # A: flat single-segment path
        if len(segments) == 1:
            return resolve(segments[0], index, frag, "A")
        # C: known bogus section prefix
        if segments[0] in KNOWN_PREFIXES:
            return resolve(segments[-1], index, frag, "C")
        return None, "skip"

    # E: bare relative slug, no leading slash
    if re.fullmatch(r"[a-z0-9][a-z0-9-]*", base):
        return resolve(base, index, frag, "E")

    return None, "skip"


def process(path, index, counters, examples, unresolved, blocked):
    raw = open(path, encoding="utf-8").read()
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return raw, 0
    head, body = raw[: len(parts[0]) + len(parts[1]) + 6], parts[2]

    masked = mask_code(body)
    edits = []
    seen_at = set()
    hits = list(LINK_RE.finditer(masked)) + list(HREF_RE.finditer(masked))
    for m in sorted(hits, key=lambda x: x.start(1)):
        target = m.group(1)
        start = m.start(1)
        # Both regexes can land on the same target. Never edit an offset twice.
        if start in seen_at:
            continue
        new, tag = classify(target, index)
        if new is None:
            if tag == "unpublished":
                unresolved[target] += 1
            elif tag == "duplicate":
                blocked[target] += 1
            continue
        # The masked copy is length-preserving, so the same offset in the real
        # body must hold the identical target. If it does not, skip rather than
        # risk a bad write.
        if body[start:start + len(target)] != target:
            continue
        seen_at.add(start)
        edits.append((start, len(target), new, tag, target))

    if not edits:
        return raw, 0

    out = []
    cursor = 0
    for start, length, new, tag, old in edits:
        out.append(body[cursor:start])
        out.append(new)
        cursor = start + length
        counters[tag] += 1
        if len(examples[tag]) < 3:
            examples[tag].append((os.path.basename(path), old, new))
    out.append(body[cursor:])
    return head + "".join(out), len(edits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes to disk")
    ap.add_argument("--posts", default=POSTS_DIR)
    args = ap.parse_args()

    if not os.path.isdir(args.posts):
        sys.exit("posts directory not found: %s" % args.posts)

    index, duplicates = build_slug_index(args.posts)
    counters, unresolved, blocked = Counter(), Counter(), Counter()
    examples = defaultdict(list)
    touched, total = 0, 0

    for name in sorted(os.listdir(args.posts)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(args.posts, name)
        new_text, n = process(path, index, counters, examples, unresolved, blocked)
        if n:
            touched += 1
            total += n
            if args.apply:
                open(path, "w", encoding="utf-8").write(new_text)

    names = {
        "A": "flat path",
        "B": "right slug, wrong date",
        "C": "bogus section prefix",
        "D": "filename pasted as link",
        "E": "no leading slash",
    }
    mode = "APPLIED" if args.apply else "DRY RUN"
    print("=" * 62)
    print("fix_permalinks.py  [%s]" % mode)
    print("=" * 62)
    print("posts scanned            : %d" % len(os.listdir(args.posts)))
    print("slugs indexed            : %d" % len(index))
    if duplicates:
        print("duplicate slugs (2 files): %d  -> %s" % (len(duplicates), ", ".join(duplicates)))
    print()
    for tag in "ABCDE":
        print("  %s  %-26s %5d" % (tag, names[tag], counters[tag]))
    print("  %-31s %5d" % ("TOTAL LINKS REWRITTEN", total))
    print("  %-31s %5d" % ("POSTS TOUCHED", touched))
    print()
    print("left untouched, target not yet published: %d links, %d targets"
          % (sum(unresolved.values()), len(unresolved)))
    if blocked:
        print("BLOCKED, duplicate slug so the date cannot be inferred: %d links, %d targets"
              % (sum(blocked.values()), len(blocked)))
        for t, n in blocked.most_common():
            print("    %-58s x%d" % (t, n))
    print()
    for tag in "ABCDE":
        if examples[tag]:
            print("--- %s: %s" % (tag, names[tag]))
            for fn, old, new in examples[tag]:
                print("    %s" % fn)
                print("      %s" % old)
                print("   -> %s" % new)
    if not args.apply:
        print()
        print("nothing written. rerun with --apply to write." if total
              else "nothing to change.")


if __name__ == "__main__":
    main()
