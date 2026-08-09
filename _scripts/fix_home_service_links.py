#!/usr/bin/env python3
"""
Group A repair.

Repoints every link to the never-built page

    https://reportmedic.org/tools/home-service-cost-tools.html

to the page that already exists and already does the job

    https://vaultbook.net/tools/home-project-planner.html

and, because every one of these links says "on ReportMedic" in its anchor
text, rewrites ReportMedic to VaultBook INSIDE THE ANCHOR TEXT OF THE
MATCHED LINK ONLY. No other mention of ReportMedic anywhere in the post is
touched.

Affects 18 links across 17 posts. Safe to run repeatedly. Dry run by default.

    python3 _scripts/fix_home_service_links.py            # dry run
    python3 _scripts/fix_home_service_links.py --apply    # write changes
"""

import argparse
import os
import re
import sys

OLD = "https://reportmedic.org/tools/home-service-cost-tools.html"
NEW = "https://vaultbook.net/tools/home-project-planner.html"

# Matches a full markdown link whose target is the old URL, capturing the
# anchor text so it can be corrected in the same pass.
LINK = re.compile(
    r"\[(?P<text>[^\]]*)\]\(" + re.escape(OLD) + r"(?P<frag>[^)]*)\)"
)


def fix_link(m):
    text = m.group("text")
    # Only inside this anchor text, and only the brand word.
    text = re.sub(r"\bReportMedic\b", "VaultBook", text)
    return "[" + text + "](" + NEW + m.group("frag") + ")"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes to disk")
    ap.add_argument("--posts", default="_posts")
    args = ap.parse_args()

    if not os.path.isdir(args.posts):
        sys.exit("Posts directory not found: " + args.posts)

    total = 0
    changed = []
    renamed = 0

    for name in sorted(os.listdir(args.posts)):
        if not name.endswith(".md"):
            continue
        p = os.path.join(args.posts, name)
        with open(p, encoding="utf-8") as fh:
            original = fh.read()

        found = LINK.findall(original)
        if not found:
            continue
        renamed += sum(1 for t, _ in found if "ReportMedic" in t)

        updated = LINK.sub(fix_link, original)
        total += len(found)
        changed.append((name, len(found)))
        if args.apply:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(updated)

    mode = "APPLIED" if args.apply else "DRY RUN"
    print("=" * 64)
    print("  Group A: home-service-cost-tools  ->  home-project-planner")
    print("  " + mode)
    print("=" * 64)
    if not total:
        print("  Nothing to change. Already repointed.")
        return
    for name, n in changed:
        print(f"  {n}  {name}")
    print("-" * 64)
    print(f"  {total} links across {len(changed)} posts")
    print(f"  {renamed} anchor texts had ReportMedic corrected to VaultBook")
    if not args.apply:
        print("  Re-run with --apply to write these changes.")


if __name__ == "__main__":
    main()
