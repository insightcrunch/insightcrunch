#!/usr/bin/env python3
"""
extract_links.py - Scan all Jekyll posts and extract hyperlinks.

Outputs admin/links-data.json with every link found in every post,
grouped by post. The admin Broken Links tool loads this JSON and
lets you check link health from the browser.

Run during scheduled/manual builds alongside keyword_audit.py.
"""

import json
import os
import re
import sys
from pathlib import Path

POSTS_DIR = Path("_posts")
OUTPUT = Path("admin/links-data.json")

# Regex patterns for link extraction
# Markdown links: [text](url) and [text](url "title")
MD_LINK = re.compile(r'\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
# Raw URLs (http/https) not already inside markdown link parens
RAW_URL = re.compile(r'(?<!\()(https?://[^\s\)<>\[\]"\'`]+)')
# HTML href links in raw HTML within markdown
HTML_HREF = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)

# Ignore patterns - asset links, anchors, mailto, liquid tags
IGNORE_PATTERNS = [
    re.compile(r'^#'),                    # anchor-only
    re.compile(r'^mailto:', re.I),        # email
    re.compile(r'^tel:', re.I),           # phone
    re.compile(r'^javascript:', re.I),    # js
    re.compile(r'\{\{'),                  # liquid variable
    re.compile(r'\{%'),                   # liquid tag
    re.compile(r'\.(png|jpg|jpeg|gif|svg|webp|ico|mp4|mp3|pdf|zip)$', re.I),  # media/files
]


def should_ignore(url):
    """Return True if this URL should be skipped."""
    for pat in IGNORE_PATTERNS:
        if pat.search(url):
            return True
    return False


def classify_link(href):
    """Classify a link as internal or external."""
    if href.startswith(("http://", "https://")):
        # Check if it points to insightcrunch.com
        if "insightcrunch.com" in href:
            return "internal"
        return "external"
    if href.startswith("/"):
        return "internal"
    # Relative links
    return "internal"


def extract_links_from_content(content):
    """Extract all unique links from markdown content, ignoring frontmatter."""
    # Strip frontmatter
    fm_match = re.match(r'^---\s*\n[\s\S]*?\n---\s*\n([\s\S]*)$', content)
    body = fm_match.group(1) if fm_match else content

    # Strip liquid comments and code blocks (don't scan inside them)
    body = re.sub(r'{%\s*comment\s*%}[\s\S]*?{%\s*endcomment\s*%}', '', body)
    body = re.sub(r'```[\s\S]*?```', '', body)
    body = re.sub(r'`[^`]+`', '', body)

    links = {}  # href -> {text, type}

    # Markdown links
    for match in MD_LINK.finditer(body):
        text, href = match.group(1).strip(), match.group(2).strip()
        if href and not should_ignore(href):
            if href not in links:
                links[href] = {"text": text, "href": href, "type": classify_link(href)}

    # HTML href attributes
    for match in HTML_HREF.finditer(body):
        href = match.group(1).strip()
        if href and not should_ignore(href):
            if href not in links:
                links[href] = {"text": "", "href": href, "type": classify_link(href)}

    # Raw URLs not already captured
    for match in RAW_URL.finditer(body):
        href = match.group(0).strip().rstrip(".,;:!?)")
        if href and not should_ignore(href):
            if href not in links:
                links[href] = {"text": "", "href": href, "type": classify_link(href)}

    return list(links.values())


def parse_frontmatter(content):
    """Extract title, categories, date from frontmatter."""
    fm = {}
    fm_match = re.match(r'^---\s*\n([\s\S]*?)\n---', content)
    if fm_match:
        for line in fm_match.group(1).split("\n"):
            kv = re.match(r'^(\w[\w-]*):\s*(.+)$', line)
            if kv:
                key, val = kv.group(1), kv.group(2).strip().strip('"').strip("'")
                fm[key] = val
    return fm


def main():
    if not POSTS_DIR.exists():
        print(f"Error: {POSTS_DIR} not found. Run from repo root.", file=sys.stderr)
        sys.exit(1)

    results = []
    md_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    print(f"Scanning {len(md_files)} posts for links...")

    total_links = 0
    posts_with_links = 0

    for filepath in md_files:
        filename = filepath.name
        date_match = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)\.md$', filename)
        if not date_match:
            continue

        date_str = date_match.group(1)
        slug = date_match.group(2)

        content = filepath.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        title = fm.get("title", slug.replace("-", " ").title())

        links = extract_links_from_content(content)

        if links:
            posts_with_links += 1
            total_links += len(links)

        url = f"/{date_str.replace('-', '/')}/{slug}/"

        results.append({
            "slug": slug,
            "title": title,
            "url": url,
            "date": date_str,
            "linkCount": len(links),
            "internal": sum(1 for l in links if l["type"] == "internal"),
            "external": sum(1 for l in links if l["type"] == "external"),
            "links": links,
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")

    print(f"Done. {posts_with_links} posts with links, {total_links} total links.")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
