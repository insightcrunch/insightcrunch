#!/usr/bin/env python3
"""
fix_prefixed_links.py

ONE-TIME repair. Not part of the build.

Goal: no internal link on insightcrunch.com is left in a shape that can never
resolve. Three broken shapes remain after fix_permalinks.py:

    /blog/<slug>        and /insights/<slug>
    /a-levels/<slug>    and other invented section prefixes
    /<slug>             flat, no date

None of these carry a date, so unlike a dated forward link they do NOT start
working when the target article is published. They are permanent 404s.

Each broken link gets exactly one of three treatments:

  1 REWRITE   The slug appears in a locked slug/date table in the
              insightcrunch-prompts repo. Rewrite to /YYYY/MM/DD/<slug>/ using
              the table date. The article is planned for that exact date, so
              the link goes live the day it publishes.

  2 ALIAS     The slug does not appear in any table, but a hand-checked
              equivalent article exists, either published or in a table. Point
              the link at that article. Every alias below was verified one by
              one against _posts and the tables. No fuzzy matching is used.

  3 UNLINK    The slug appears in no table and has no equivalent article. A
              date cannot be invented, because inventing one produces a URL
              that will never exist. The link markup is removed and the anchor
              text is kept as plain prose, so the sentence still reads
              correctly and the broken link is gone.

Code fences are blanked with LENGTH-PRESERVING whitespace before scanning, so
offsets stay valid and code samples are never touched.

Usage:
    python3 _scripts/fix_prefixed_links.py            dry run
    python3 _scripts/fix_prefixed_links.py --apply    writes the files

Requires SLUG_DATE_MAP.json in the repo root, generated from the prompts repo.

Idempotent. A second run reports nothing to change.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

POSTS_DIR = "_posts"
MAP_FILE = "SLUG_DATE_MAP.json"

# Section prefixes that were written into prose but never existed on the site.
BOGUS_PREFIXES = {
    "blog", "insights", "a-levels", "posts", "sat", "articles", "category",
    "classic-literature-200", "harry-potter-character-analysis",
    "bollywood-cinema-authority", "us-presidents", "reportmedic",
}

# Real site sections. A link starting with one of these is left alone.
REAL_PREFIXES = {"assets", "tools", "admin", "tag", "tags"}

# Treatment 2. Every entry checked by hand against _posts and the locked
# tables. Left side is what prose was written as, right side is the article
# that actually serves the intent.
ALIASES = {
    # malformed date, the slug is a published post
    "02-28-edmund-king-lear-character-analysis": "edmund-king-lear-character-analysis",
    "10-gloucester-king-lear-character-analysis": "gloucester-king-lear-character-analysis",
    # near-miss slugs, target published
    "upsc-civil-services-exam-complete-guide": "upsc-civil-services-complete-guide",
    "ap-exams-guide": "ap-exams-complete-guide",
    "hermione-deep-dive": "hermione-granger-complete-character-analysis",
    "presidential-pardon-washington-to-clinton": "presidential-pardon-two-centuries",
    "sat-transition-questions": "sat-transitions-logical-flow-questions-guide",
    "sat-error-categories": "sat-error-analysis-mistake-journal-guide",
    "if-eisenhower-intervened-dien-bien-phu-1954": "eisenhower-dien-bien-phu-refusal-1954",
    # near-miss slugs, target in a locked table
    "stalingrad-hitler-no-retreat-order-1942": "stalingrad-hitler-no-retreat-order-november-1942",
    "a-level-guide": "a-level-complete-guide",
    "allied-axis-intelligence-comparison": "allied-vs-axis-intelligence-capabilities",
    "van-buren-amistad-decision-1839": "van-buren-amistad-1841",
}

# Links that are correct as written and must never be rewritten. These are real
# pages that are not posts, so a slug lookup would wrongly flag them.
KEEP_AS_IS = {
    "/category/ap/",
    "/category/ap",
}

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$")
LINK_RE = re.compile(r"\[((?:[^\]\[]|\[[^\]]*\])*)\]\(([^)\s]+)(\s+\"[^\"]*\")?\)")


def blank(match):
    return "".join("\n" if c == "\n" else " " for c in match.group(0))


def mask_code(body):
    body = re.sub(r"```.*?```", blank, body, flags=re.S)
    body = re.sub(r"~~~.*?~~~", blank, body, flags=re.S)
    body = re.sub(r"`[^`\n]*`", blank, body)
    return body


def build_post_index(posts_dir):
    seen = defaultdict(set)
    for name in os.listdir(posts_dir):
        m = FILENAME_RE.match(name)
        if m:
            seen[m.group(4)].add((m.group(1), m.group(2), m.group(3)))
    return {slug: sorted(dates) for slug, dates in seen.items()}


def dated(slug, date):
    return "/%s/%s/%s/%s/" % (date[0], date[1], date[2], slug)


def resolve(slug, posts, table):
    """Return a working URL for this slug, or None."""
    dates = posts.get(slug)
    if dates and len(dates) == 1:
        return dated(slug, dates[0])
    if dates and len(dates) > 1:
        return None  # duplicate slug, never guess
    entry = table.get(slug)
    if entry:
        y, mo, d = entry[0].split("-")
        return dated(slug, (y, mo, d))
    return None


def classify(target, posts, table):
    """Return (action, new_target). Action is rewrite, alias, unlink or skip."""
    base = target.split("#", 1)[0].split("?", 1)[0]
    frag = target[len(base):]

    if base in KEEP_AS_IS or not base.startswith("/") or base in ("/", ""):
        return "skip", None
    if re.match(r"^/\d{4}/\d{2}/\d{2}/[^/]+/?$", base):
        return "skip", None

    segments = [s for s in base.strip("/").split("/") if s]
    if not segments:
        return "skip", None

    # Malformed dated paths, where a slash became a hyphen:
    #   /2011/02-28-edmund-king-lear-character-analysis/
    #   /2011/03/10-gloucester-king-lear-character-analysis/
    # The slug is recoverable by stripping the leading date fragments.
    if re.fullmatch(r"\d{4}", segments[0]):
        tail = segments[-1]
        stripped = re.sub(r"^(?:\d{2}-){1,2}", "", tail)
        stripped = re.sub(r"^\d{2}-", "", stripped)
        if stripped != tail:
            url = resolve(stripped, posts, table)
            if url:
                return "rewrite", url + frag
        return "skip", None
    if segments[0] in REAL_PREFIXES:
        return "skip", None
    if len(segments) > 1 and segments[0] not in BOGUS_PREFIXES:
        return "skip", None

    slug = segments[-1]

    url = resolve(slug, posts, table)
    if url:
        return "rewrite", url + frag

    if slug in ALIASES:
        url = resolve(ALIASES[slug], posts, table)
        if url:
            return "alias", url + frag

    return "unlink", None


def process(path, posts, table, counters, examples, unlinked):
    raw = open(path, encoding="utf-8").read()
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return raw, 0
    head = raw[: len(parts[0]) + len(parts[1]) + 6]
    body = parts[2]

    masked = mask_code(body)
    edits = []
    for m in LINK_RE.finditer(masked):
        anchor, target = m.group(1), m.group(2)
        action, new = classify(target, posts, table)
        if action == "skip":
            continue
        start, end = m.start(), m.end()
        if body[start:end] != masked[start:end]:
            continue  # offset mismatch, refuse to touch
        if action in ("rewrite", "alias"):
            replacement = "[%s](%s)" % (anchor, new)
        else:
            replacement = anchor
            unlinked[target.strip("/").split("/")[-1]] += 1
        edits.append((start, end, replacement, action, target))

    if not edits:
        return raw, 0

    out, cursor = [], 0
    for start, end, replacement, action, old in edits:
        out.append(body[cursor:start])
        out.append(replacement)
        cursor = end
        counters[action] += 1
        if len(examples[action]) < 4:
            examples[action].append((os.path.basename(path), old, replacement[:100]))
    out.append(body[cursor:])
    return head + "".join(out), len(edits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes to disk")
    ap.add_argument("--posts", default=POSTS_DIR)
    ap.add_argument("--map", default=MAP_FILE)
    args = ap.parse_args()

    if not os.path.isdir(args.posts):
        sys.exit("posts directory not found: %s" % args.posts)
    if not os.path.exists(args.map):
        sys.exit("slug map not found: %s" % args.map)

    table = json.load(open(args.map, encoding="utf-8"))
    posts = build_post_index(args.posts)

    counters, unlinked = Counter(), Counter()
    examples = defaultdict(list)
    touched = total = 0

    for name in sorted(os.listdir(args.posts)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(args.posts, name)
        new_text, n = process(path, posts, table, counters, examples, unlinked)
        if n:
            touched += 1
            total += n
            if args.apply:
                open(path, "w", encoding="utf-8").write(new_text)

    mode = "APPLIED" if args.apply else "DRY RUN"
    print("=" * 66)
    print("fix_prefixed_links.py  [%s]" % mode)
    print("=" * 66)
    print("posts scanned         : %d" % len(os.listdir(args.posts)))
    print("published slugs       : %d" % len(posts))
    print("slugs in locked tables: %d" % len(table))
    print()
    labels = {"rewrite": "rewritten from locked table",
              "alias": "repointed via checked alias",
              "unlink": "unlinked, anchor text kept"}
    for tag in ("rewrite", "alias", "unlink"):
        print("  %-32s %5d" % (labels[tag], counters[tag]))
    print("  %-32s %5d" % ("TOTAL LINKS CHANGED", total))
    print("  %-32s %5d" % ("POSTS TOUCHED", touched))
    print()
    for tag in ("rewrite", "alias", "unlink"):
        if examples[tag]:
            print("--- %s" % labels[tag])
            for fn, old, new in examples[tag]:
                print("    %s" % fn)
                print("      %s" % old)
                print("   -> %s" % new)
            print()
    if unlinked:
        print("unlinked targets, %d distinct:" % len(unlinked))
        for t, n in unlinked.most_common():
            print("    %-54s x%d" % (t, n))
    if not args.apply:
        print()
        print("nothing written. rerun with --apply to write." if total
              else "nothing to change.")


if __name__ == "__main__":
    main()
