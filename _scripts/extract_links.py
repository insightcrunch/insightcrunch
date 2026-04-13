#!/usr/bin/env python3
"""
extract_links.py - Scan all Jekyll posts, extract hyperlinks, and check them.

Runs at build time. For each post in _posts/:
  - Extracts markdown links, HTML hrefs, and raw URLs
  - Checks internal links against ALL known post slugs (published + future)
  - Checks external links via HEAD requests (concurrent, with cache)

Outputs:
  admin/links-data.json          - full link data with statuses (admin page)
  _data/links_check_cache.json   - persistent cache so verified links are skipped

Cache entries expire after 14 days. First run checks everything (may take
a few minutes). Subsequent runs only check new or expired links.
"""

import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

POSTS_DIR = Path("_posts")
OUTPUT = Path("admin/links-data.json")
CACHE_FILE = Path("_data/links_check_cache.json")
CACHE_EXPIRY_DAYS = 14
MAX_CONCURRENT = 30
REQUEST_TIMEOUT = 8
MAX_CHECK_TIME = 300  # 5 min ceiling for external checks

MD_LINK = re.compile(r'\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
RAW_URL = re.compile(r'(?<!\()(https?://[^\s\)<>\[\]"\'`]+)')
HTML_HREF = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
POST_URL_PAT = re.compile(r'^/?(\d{4})/(\d{2})/(\d{2})/([\w-]+)/?$')

IGNORE_PATTERNS = [
    re.compile(r'^#'),
    re.compile(r'^mailto:', re.I),
    re.compile(r'^tel:', re.I),
    re.compile(r'^javascript:', re.I),
    re.compile(r'\{\{'),
    re.compile(r'\{%'),
    re.compile(r'\.(png|jpg|jpeg|gif|svg|webp|ico|mp4|mp3|pdf|zip|css|js)$', re.I),
]


def should_ignore(url):
    for pat in IGNORE_PATTERNS:
        if pat.search(url):
            return True
    return False


def classify_link(href):
    if href.startswith(("http://", "https://")):
        if "insightcrunch.com" in href:
            return "internal"
        return "external"
    if href.startswith("/"):
        return "internal"
    return "internal"


def extract_links(content):
    fm_match = re.match(r'^---\s*\n[\s\S]*?\n---\s*\n([\s\S]*)$', content)
    body = fm_match.group(1) if fm_match else content
    body = re.sub(r'{%\s*comment\s*%}[\s\S]*?{%\s*endcomment\s*%}', '', body)
    body = re.sub(r'```[\s\S]*?```', '', body)
    body = re.sub(r'`[^`]+`', '', body)

    links = {}
    for m in MD_LINK.finditer(body):
        text, href = m.group(1).strip(), m.group(2).strip()
        if href and not should_ignore(href) and href not in links:
            links[href] = {"text": text, "href": href, "type": classify_link(href)}
    for m in HTML_HREF.finditer(body):
        href = m.group(1).strip()
        if href and not should_ignore(href) and href not in links:
            links[href] = {"text": "", "href": href, "type": classify_link(href)}
    for m in RAW_URL.finditer(body):
        href = m.group(0).strip().rstrip(".,;:!?)")
        if href and not should_ignore(href) and href not in links:
            links[href] = {"text": "", "href": href, "type": classify_link(href)}
    return list(links.values())


def parse_frontmatter(content):
    fm = {}
    fm_match = re.match(r'^---\s*\n([\s\S]*?)\n---', content)
    if fm_match:
        for line in fm_match.group(1).split("\n"):
            kv = re.match(r'^(\w[\w-]*):\s*(.+)$', line)
            if kv:
                fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return fm


def build_known_urls(md_files):
    """All post URLs from _posts/ including future-dated files."""
    known = set()
    pat = re.compile(r'^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$')
    for f in md_files:
        m = pat.match(f.name)
        if not m:
            continue
        url = f"/{m.group(1)}/{m.group(2)}/{m.group(3)}/{m.group(4)}/"
        known.add(url)
        known.add(url.rstrip("/"))
    return known


def check_internal(href, known_urls):
    path = href
    if "insightcrunch.com" in href:
        try:
            path = urlparse(href).path
        except Exception:
            pass

    norm = path.rstrip("/")
    norm_slash = path if path.endswith("/") else path + "/"
    if path in known_urls or norm in known_urls or norm_slash in known_urls:
        return {"status": "ok", "detail": "Post exists"}

    if POST_URL_PAT.match(path):
        return {"status": "broken", "detail": "Post not found in _posts/"}

    return {"status": "unknown", "detail": "Non-post page (not verifiable)"}


def check_external(href):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    last_error = None

    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(href, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
                code = resp.getcode()
                if 200 <= code < 400:
                    return {"status": "ok", "detail": f"HTTP {code}"}
                if method == "GET":
                    return {"status": "broken", "detail": f"HTTP {code}"}
        except urllib.error.HTTPError as e:
            if e.code in (403, 405, 406, 429):
                return {"status": "unknown", "detail": f"HTTP {e.code} (may block bots)"}
            if 400 <= e.code < 500:
                if method == "HEAD":
                    last_error = f"HTTP {e.code}"
                    continue
                return {"status": "broken", "detail": f"HTTP {e.code}"}
            if method == "HEAD":
                last_error = f"HTTP {e.code} (server error)"
                continue
            return {"status": "unknown", "detail": f"HTTP {e.code} (server error)"}
        except urllib.error.URLError as e:
            reason = str(getattr(e, "reason", e))
            if "timeout" in reason.lower() or "timed out" in reason.lower():
                if method == "HEAD":
                    last_error = "Timeout"
                    continue
                return {"status": "unknown", "detail": "Timeout"}
            if method == "HEAD":
                last_error = reason[:80]
                continue
            return {"status": "broken", "detail": reason[:80]}
        except Exception as e:
            msg = str(e)[:80]
            if method == "HEAD":
                last_error = msg
                continue
            return {"status": "unknown" if "timeout" in msg.lower() else "broken", "detail": msg}

    return {"status": "broken", "detail": last_error or "Both HEAD and GET failed"}


def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def main():
    if not POSTS_DIR.exists():
        print(f"Error: {POSTS_DIR} not found. Run from repo root.", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    print(f"Scanning {len(md_files)} posts for links...")

    known_urls = build_known_urls(md_files)
    print(f"Indexed {len(known_urls) // 2} post URLs (published + future)")

    # --- Extract ---
    results = []
    all_external = set()

    for filepath in md_files:
        m = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)\.md$', filepath.name)
        if not m:
            continue
        date_str, slug = m.group(1), m.group(2)
        content = filepath.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        title = fm.get("title", slug.replace("-", " ").title())
        links = extract_links(content)
        for l in links:
            if l["type"] == "external":
                all_external.add(l["href"])
        results.append({
            "slug": slug, "title": title,
            "url": f"/{date_str.replace('-', '/')}/{slug}/",
            "date": date_str,
            "linkCount": len(links),
            "internal": sum(1 for l in links if l["type"] == "internal"),
            "external": sum(1 for l in links if l["type"] == "external"),
            "links": links,
        })

    # --- Check internal (instant) ---
    print("Checking internal links...")
    int_results = {}
    for post in results:
        for l in post["links"]:
            if l["type"] == "internal" and l["href"] not in int_results:
                int_results[l["href"]] = check_internal(l["href"], known_urls)

    # --- Check external (concurrent + cached) ---
    cache = load_cache()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cutoff = (datetime.utcnow() - timedelta(days=CACHE_EXPIRY_DAYS)).strftime("%Y-%m-%d")

    to_check = [h for h in all_external if not (cache.get(h, {}).get("checked", "") >= cutoff)]
    print(f"External links: {len(all_external)} total, {len(all_external) - len(to_check)} cached, {len(to_check)} to check")

    if to_check:
        t0 = time.time()
        done = 0
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as pool:
            futs = {pool.submit(check_external, h): h for h in to_check}
            for fut in as_completed(futs):
                if time.time() - t0 > MAX_CHECK_TIME:
                    print(f"  Hit {MAX_CHECK_TIME}s time limit after {done}/{len(to_check)} links")
                    break
                href = futs[fut]
                try:
                    res = fut.result(timeout=REQUEST_TIMEOUT + 2)
                except Exception as e:
                    res = {"status": "unknown", "detail": str(e)[:80]}
                cache[href] = {**res, "checked": today}
                done += 1
                if done % 100 == 0:
                    print(f"  {done}/{len(to_check)} checked ({time.time() - t0:.0f}s)")
        print(f"  Finished: {done} links in {time.time() - t0:.1f}s")

    save_cache(cache)

    # --- Merge statuses ---
    ext_results = {}
    for h in all_external:
        c = cache.get(h)
        ext_results[h] = {"status": c["status"], "detail": c["detail"]} if c else {"status": "unchecked", "detail": "Not yet checked"}

    total_broken = total_ok = 0
    for post in results:
        broken = ok = unknown = 0
        for l in post["links"]:
            r = int_results.get(l["href"]) if l["type"] == "internal" else ext_results.get(l["href"], {"status": "unchecked", "detail": ""})
            l["status"] = r["status"]
            l["detail"] = r["detail"]
            if r["status"] == "broken": broken += 1
            elif r["status"] == "ok": ok += 1
            else: unknown += 1
        post["brokenCount"] = broken
        post["okCount"] = ok
        post["unknownCount"] = unknown
        total_broken += broken
        total_ok += ok

    total_links = sum(p["linkCount"] for p in results)
    output_data = {"generated": today, "postCount": len(results), "posts": results}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output_data, ensure_ascii=False), encoding="utf-8")

    print(f"\nDone. {sum(1 for p in results if p['linkCount'] > 0)} posts with links, {total_links} total.")
    print(f"  {total_ok} ok | {total_broken} broken | {total_links - total_ok - total_broken} unknown/unchecked")
    print(f"Output: {OUTPUT}")
    print(f"Cache:  {CACHE_FILE} ({len(cache)} entries)")


if __name__ == "__main__":
    main()
