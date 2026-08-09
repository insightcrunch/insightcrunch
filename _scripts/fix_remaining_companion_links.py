#!/usr/bin/env python3
"""
Final companion link repair for insightcrunch.com.

Every remaining broken companion link points at a page that ALREADY EXISTS.
Nothing here creates or deletes a page. Each entry rewrites a link so it
resolves, and where the repoint crosses domains it also corrects the brand
word inside that link's anchor text.

Covers 32 broken paths across roughly 45 posts and 62 links:

  Group D  malformed URLs, page already live      21 posts
  Group E  WWII medical topics, sections of one   14 posts
           existing reference page
  Group C  leftovers                               4 posts

Safe to run repeatedly. Dry run by default.

    python3 _scripts/fix_remaining_companion_links.py            # dry run
    python3 _scripts/fix_remaining_companion_links.py --apply    # write
"""

import argparse
import os
import re
import sys
from collections import Counter

VB = "https://vaultbook.net"
RM = "https://reportmedic.org"

TIMELINE  = RM + "/tools/world-history-timeline.html"
LITGUIDE  = RM + "/tools/classic-literature-study-guide.html"
SHAKES    = RM + "/tools/shakespeare-character-explorer.html"
VICTORIAN = RM + "/tools/victorian-novel-comparison-toolkit.html"
WWII      = RM + "/tools/wwii-battlefield-medicine.html"
FOOTBALL  = VB + "/tools/football-match-planner.html"
GATSBY    = VB + "/tools/great-gatsby-annotated-text.html"

# path fragment as it appears in posts  ->  full absolute URL it should become
MAP = {
    # ---- Group D: malformed URLs for pages that are already live ----------
    "/world-history-timeline/":            TIMELINE,
    "/world-history-timeline":             TIMELINE,
    "/tools/timeline-analysis":            TIMELINE,
    "/timeline":                           TIMELINE,
    "/leadership-patterns-history/":       TIMELINE,

    "/classic-literature-study-guide/":    LITGUIDE,
    "/classic-literature-study-guide":     LITGUIDE,
    "/study-guides/classic-literature/":   LITGUIDE,
    "/literary-analysis-library/":         LITGUIDE,
    "/literary-analysis-tools/":           LITGUIDE,
    "/interactive-literature-tools/":      LITGUIDE,
    "/tools":                              LITGUIDE,

    "/literary-character-explorer/":       SHAKES,

    "/literary-comparison-tools/":         VICTORIAN,
    "/tools/document-comparison":          VICTORIAN,

    # ---- Group E: WWII medical topics, all sections of one live page ------
    "/history/battlefield-casualty-evacuation-dunkirk":                 WWII,
    "/history/combat-stress-1940-campaign":                             WWII,
    "/history/combat-stress-and-postwar-recovery":                      WWII,
    "/history/medicalized-killing-and-the-birth-of-informed-consent":   WWII,
    "/history/starvation-physiology-and-the-bodies-of-survivors":       WWII,
    "/history/wartime-public-health-and-the-welfare-state":             WWII,
    "/archives/military-archive-preservation":                          WWII,
    "/archives/wartime-administrative-records":                         WWII,
    "/conditions/angina-symptoms-and-causes":                           WWII,
    "/wellness/sleep-deprivation-effects":                              WWII,
    "/sleep-deprivation-decision-making":                               WWII,
    "/chronic-anxiety-wartime-civilians":                               WWII,
    "/malnutrition-infection-captivity":                                WWII,
    "/tropical-disease-siege-conditions":                               WWII,
    "/waterborne-infection-crisis-conditions":                          WWII,

    # ---- Group C: leftovers ----------------------------------------------
    "/tools/football-conditioning-safety.html":     FOOTBALL,
    "/great-gatsby/billboard-advertising-imagery":  GATSBY,
}

# Domains a broken link may currently carry, including the fake one.
DOMAINS = [
    "https://reportmedic.org", "http://reportmedic.org",
    "https://www.reportmedic.org",
    "https://vaultbook.net", "http://vaultbook.net",
    "https://www.vaultbook.net",
    "https://vaultbook.org", "http://vaultbook.org",
    "https://vaultbook.example", "https://www.vaultbook.example",
    "https://reportmedic.example",
]

BRAND = {"vaultbook.net": "VaultBook", "reportmedic.org": "ReportMedic"}


def target_brand(url):
    for host, name in BRAND.items():
        if host in url:
            return name
    return None


def build_patterns():
    """Longest paths first so /world-history-timeline/ wins over /world-history-timeline."""
    pats = []
    for path, target in sorted(MAP.items(), key=lambda kv: len(kv[0]), reverse=True):
        for dom in DOMAINS:
            old = dom + path
            # A full markdown link, so the anchor text can be corrected too.
            # (?![A-Za-z0-9._/-]) stops a short path matching a longer one.
            rx = re.compile(
                r"\[(?P<text>[^\]]*)\]\("
                + re.escape(old)
                + r"(?![A-Za-z0-9._/-])(?P<frag>[^)]*)\)"
            )
            pats.append((rx, target, old))
    return pats


def make_sub(target):
    want = target_brand(target)
    other = "ReportMedic" if want == "VaultBook" else "VaultBook"

    def sub(m):
        text = m.group("text")
        if want:
            # Only inside this anchor text, and only the brand word.
            text = re.sub(r"\b" + other + r"\b", want, text)
        return "[" + text + "](" + target + m.group("frag") + ")"

    return sub


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes to disk")
    ap.add_argument("--posts", default="_posts")
    args = ap.parse_args()

    if not os.path.isdir(args.posts):
        sys.exit("Posts directory not found: " + args.posts)

    pats = build_patterns()
    hits = Counter()
    brand_fixes = 0
    files = []

    for name in sorted(os.listdir(args.posts)):
        if not name.endswith(".md"):
            continue
        p = os.path.join(args.posts, name)
        with open(p, encoding="utf-8") as fh:
            original = fh.read()

        updated = original
        for rx, target, label in pats:
            found = rx.findall(updated)
            if not found:
                continue
            want = target_brand(target)
            other = "ReportMedic" if want == "VaultBook" else "VaultBook"
            brand_fixes += sum(1 for t, _ in found if want and re.search(r"\b" + other + r"\b", t))
            updated = rx.sub(make_sub(target), updated)
            hits[label] += len(found)

        if updated != original:
            files.append(name)
            if args.apply:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(updated)

    total = sum(hits.values())
    print("=" * 74)
    print("  Final companion link repair - " + ("APPLIED" if args.apply else "DRY RUN"))
    print("=" * 74)
    if not total:
        print("  Nothing to change. Every mapped path already resolves.")
        return
    for label, n in hits.most_common():
        print(f"  {n:>3}  {label}")
    print("-" * 74)
    print(f"  {total} links across {len(files)} posts")
    print(f"  {brand_fixes} anchor texts had the brand word corrected")
    if not args.apply:
        print("  Re-run with --apply to write these changes.")


if __name__ == "__main__":
    main()
