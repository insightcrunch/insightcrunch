#!/usr/bin/env python3
"""
assign_authors.py
=================
One-time (or re-runnable) script that reads all posts, applies rules
from author_rules.yml, and writes the author slug into each post's
frontmatter. Also generates _data/post_authors.yml as a lookup table
for the layout.

Usage:
    python3 _scripts/assign_authors.py

What it does:
    1. Loads _data/authors_pool.yml  (100 author personas)
    2. Loads _data/author_rules.yml  (matching rules + default)
    3. Scans every .md file in _posts/
    4. For each post, checks title + tags + categories against rules
    5. Picks an author from the matched pool using a deterministic
       hash of the post slug (so re-runs produce the same result)
    6. Writes the author slug into the post frontmatter (author: field)
    7. Generates _data/post_authors.yml mapping slug -> author key

Re-running is safe: it overwrites previous assignments deterministically.
"""

import os
import re
import hashlib
import yaml

# ── Paths ────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(BASE, "_posts")
DATA_DIR = os.path.join(BASE, "_data")
POOL_FILE = os.path.join(DATA_DIR, "authors_pool.yml")
RULES_FILE = os.path.join(DATA_DIR, "author_rules.yml")
OUTPUT_FILE = os.path.join(DATA_DIR, "post_authors.yml")


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_frontmatter(filepath):
    """Return (frontmatter_dict, raw_text) from a Jekyll post."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Match YAML frontmatter between --- markers
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None, text

    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, text

    return fm, text


def extract_slug(filename):
    """Extract slug from filename like 2026-03-15-some-post-title.md"""
    # Remove date prefix and extension
    name = os.path.basename(filename)
    parts = name.split("-", 3)
    if len(parts) >= 4:
        slug = parts[3].replace(".md", "").replace(".markdown", "")
    else:
        slug = name.replace(".md", "").replace(".markdown", "")
    return slug


def match_keywords_in_text(keywords, text):
    """Check if any keyword appears in text as a whole word (case-insensitive).
    Uses word boundaries to prevent 'uri' matching inside 'restructuring'."""
    for kw in keywords:
        # Build pattern: word boundary on each side for ASCII keywords,
        # simple containment for CJK characters (which self-delimit)
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(kw) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def get_tags_string(fm):
    """Get all tags as a single lowercase string."""
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    return " ".join(str(t) for t in tags).lower()


def get_categories_list(fm):
    """Get categories as a list of lowercase strings."""
    cats = fm.get("categories", [])
    if isinstance(cats, str):
        cats = [cats]
    return [str(c).lower().strip() for c in cats]


def find_matching_pool(fm, rules_data):
    """Apply rules in order. Return the pool name for the first match."""
    title = str(fm.get("title", "") or fm.get("page_title", ""))
    tags_str = get_tags_string(fm)
    cats = get_categories_list(fm)

    for rule in rules_data.get("rules", []):
        keywords = rule.get("keywords", [])
        scope = rule.get("scope", "any")
        rule_cats = rule.get("categories", [])

        # Category-only rules (fallback level)
        if rule_cats and not keywords:
            for rc in rule_cats:
                if rc.lower() in cats:
                    return rule["pool"]
            continue

        # Keyword rules
        if keywords:
            matched = False

            if scope in ("title", "any"):
                if match_keywords_in_text(keywords, title):
                    matched = True

            if not matched and scope in ("tags", "any"):
                if match_keywords_in_text(keywords, tags_str):
                    matched = True

            if not matched and scope in ("categories", "any"):
                cats_str = " ".join(cats)
                if match_keywords_in_text(keywords, cats_str):
                    matched = True

            if matched:
                return rule["pool"]

    return None


def pick_author_from_pool(pool_name, slug, authors_pool):
    """Deterministically pick an author from a pool using hash of slug."""
    # Filter authors belonging to this pool
    pool_authors = [
        key for key, data in authors_pool.items()
        if data.get("pool") == pool_name
    ]

    if not pool_authors:
        return None

    # Sort for deterministic ordering
    pool_authors.sort()

    # Hash the slug to get a stable index
    hash_val = int(hashlib.md5(slug.encode("utf-8")).hexdigest(), 16)
    idx = hash_val % len(pool_authors)

    return pool_authors[idx]


def update_frontmatter_author(filepath, new_author_slug):
    """Rewrite the author field in a post's frontmatter."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Match frontmatter block
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", text, re.DOTALL)
    if not m:
        return False

    fm_text = m.group(2)

    # Replace or add author field
    if re.search(r"^author\s*:", fm_text, re.MULTILINE):
        fm_text = re.sub(
            r'^author\s*:.*$',
            f'author: "{new_author_slug}"',
            fm_text,
            flags=re.MULTILINE
        )
    else:
        fm_text += f'\nauthor: "{new_author_slug}"'

    new_text = m.group(1) + fm_text + m.group(3) + text[m.end():]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_text)

    return True


def main():
    print("Loading authors pool...")
    authors_pool = load_yaml(POOL_FILE)

    print("Loading rules...")
    rules_data = load_yaml(RULES_FILE)

    default_author = rules_data.get("default_author", "insight-crunch-team")

    # Collect all post files
    post_files = sorted([
        os.path.join(POSTS_DIR, f)
        for f in os.listdir(POSTS_DIR)
        if f.endswith(".md") or f.endswith(".markdown")
    ])

    print(f"Found {len(post_files)} posts.")

    post_authors = {}
    pool_stats = {}
    unmatched = 0
    updated = 0
    skipped = 0

    for filepath in post_files:
        fm, _ = parse_frontmatter(filepath)
        if fm is None:
            continue

        slug = extract_slug(filepath)
        current_author = str(fm.get("author", "")).strip().strip("'\"")

        # Find which pool this post belongs to
        pool = find_matching_pool(fm, rules_data)

        if pool:
            author_key = pick_author_from_pool(pool, slug, authors_pool)
            if not author_key:
                author_key = default_author
        else:
            author_key = default_author
            unmatched += 1

        # Track stats
        pool_name = pool or "default"
        pool_stats[pool_name] = pool_stats.get(pool_name, 0) + 1

        # Only update frontmatter if author differs from expected
        if current_author != author_key:
            update_frontmatter_author(filepath, author_key)
            updated += 1
            print(f"  UPDATED: {slug}  ({current_author} -> {author_key})")
        else:
            skipped += 1

        # Record mapping
        post_authors[slug] = author_key

    # Write post_authors.yml
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(post_authors, f, default_flow_style=False, allow_unicode=True)

    # Print summary
    print("\n--- Assignment Summary ---")
    for pool_name, count in sorted(pool_stats.items(), key=lambda x: -x[1]):
        print(f"  {pool_name}: {count} posts")
    print(f"  TOTAL: {sum(pool_stats.values())} posts")
    print(f"  Updated: {updated} | Already correct: {skipped}")
    if unmatched:
        print(f"  (unmatched/default: {unmatched})")
    print(f"\nOutput written to: {OUTPUT_FILE}")
    print("Done!")


if __name__ == "__main__":
    main()
