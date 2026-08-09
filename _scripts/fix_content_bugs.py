#!/usr/bin/env python3
"""
fix_content_bugs.py

ONE-TIME repair. Three unrelated content bugs, three posts.

1. tcs-digital-interview
   A FIFO page-replacement trace was written as plain prose:

       Frame state: [1], [1,2], [2,3,4](fault), [1,2,5](hit) ... = 9 page faults.

   Kramdown reads [2,3,4](fault) as a markdown link, so nine annotations
   disappear from the rendered page and become blue links to /fault and /hit.
   Fix: wrap the trace line in a fenced code block so it renders literally.

2. is-tcs-nqt-coding-questions-tough
   A constraints line reads:

       - 1 <= P <= [1000000](tel:1000000)

   Note the character before the bracket is a non-breaking space, not a normal
   space. The match string below uses \u00a0 for that reason.

   The bound became a tappable phone link. Fix: plain text.

3. azure-functions-serverless-deep-dive
   Links to https://vaultbook.dev, a domain that is not owned. The post is
   about Azure Functions plans and scaling, so the correct target is the
   Azure labs tool on VaultBook.

Usage:
    python3 _scripts/fix_content_bugs.py            dry run
    python3 _scripts/fix_content_bugs.py --apply    writes the files

Idempotent. Every edit is an exact string match, so a second run finds nothing.
If a target string is not found the script says so and changes nothing else.
"""

import argparse
import os
import sys

POSTS_DIR = "_posts"

EDITS = [
    {
        "file": "2024-01-01-tcs-digital-interview.md",
        "label": "FIFO trace escaping",
        "old": "Frame state: [1], [1,2], [1,2,3], [2,3,4](fault), [3,4,1](fault), "
               "[4,1,2](fault), [1,2,5](fault), [1,2,5](hit), [1,2,5](hit), "
               "[2,5,3](fault), [5,3,4](fault), [3,4,5](hit) = 9 page faults.",
        "new": "```\nFrame state: [1], [1,2], [1,2,3], [2,3,4](fault), [3,4,1](fault), "
               "[4,1,2](fault), [1,2,5](fault), [1,2,5](hit), [1,2,5](hit), "
               "[2,5,3](fault), [5,3,4](fault), [3,4,5](hit) = 9 page faults.\n```",
    },
    {
        "file": "2020-04-04-is-tcs-nqt-coding-questions-tough.md",
        "label": "tel: link removal",
        "old": "- 1 <= P <=\u00a0[1000000](tel:1000000)",
        "new": "- 1 <= P <= 1000000",
    },
    {
        "file": "2022-01-24-azure-functions-serverless-deep-dive.md",
        "label": "vaultbook.dev repoint",
        "old": "[VaultBook](https://vaultbook.dev)",
        "new": "[VaultBook](https://vaultbook.net/tools/azure-labs.html)",
    },
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes to disk")
    ap.add_argument("--posts", default=POSTS_DIR)
    args = ap.parse_args()

    if not os.path.isdir(args.posts):
        sys.exit("posts directory not found: %s" % args.posts)

    mode = "APPLIED" if args.apply else "DRY RUN"
    print("=" * 62)
    print("fix_content_bugs.py  [%s]" % mode)
    print("=" * 62)

    changed = 0
    missing = 0

    for edit in EDITS:
        path = os.path.join(args.posts, edit["file"])
        print()
        print("%s" % edit["file"])
        print("  %s" % edit["label"])

        if not os.path.exists(path):
            print("  RESULT: file not found, skipped")
            missing += 1
            continue

        text = open(path, encoding="utf-8").read()

        # Checked first. On edit 1 the old string survives inside the new one,
        # so counting the old string alone would wrap the trace again on a
        # second run.
        if edit["new"] in text:
            print("  RESULT: already fixed, nothing to do")
            continue

        count = text.count(edit["old"])
        if count == 0:
            print("  RESULT: target string NOT FOUND, skipped")
            missing += 1
            continue

        print("  occurrences: %d" % count)
        print("  before: %s" % edit["old"][:90].replace("\n", " "))
        print("  after : %s" % edit["new"][:90].replace("\n", " "))

        if args.apply:
            open(path, "w", encoding="utf-8").write(text.replace(edit["old"], edit["new"]))
            print("  RESULT: written")
        else:
            print("  RESULT: would write")
        changed += 1

    print()
    print("-" * 62)
    print("files changed  : %d" % changed)
    print("files skipped  : %d" % missing)
    if not args.apply and changed:
        print("nothing written. rerun with --apply to write.")
    if missing:
        print("WARNING: at least one target was not found. Investigate before "
              "assuming the job is done.")


if __name__ == "__main__":
    main()
