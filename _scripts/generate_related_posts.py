#!/usr/bin/env python3
"""
generate_related_posts.py
=========================
Pre-build script for InsightCrunch.
Reads every post in _posts/, computes pairwise similarity scores using
category, tags (with partial matching), title tokens, and first-100-word
overlap, then writes _data/related_posts.yml so the post layout can
render a "Related Reading" section automatically.

Guarantees:
  - Every post gets 4 related links (configurable via NUM_RELATED).
  - No post is orphaned (every post appears as a related link for at
    least one other post).
  - Soft inbound cap of 10 (flexes for orphan prevention).

Run:  python _scripts/generate_related_posts.py
"""

import os
import re
import sys
import yaml
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NUM_RELATED = 4          # related links per post
INBOUND_CAP = 10         # soft max inbound links per post

# Scoring weights (must sum to 1.0)
W_CATEGORY  = 0.35
W_TAGS      = 0.30
W_CONTENT   = 0.25
W_TITLE     = 0.10

# Partial tag matching thresholds
TAG_EXACT_SCORE      = 1.0
TAG_SUBSTRING_SCORE  = 0.6
TAG_TOKEN_MIN_LEN    = 3   # ignore tokens shorter than this

# ---------------------------------------------------------------------------
# Stop words for title / content comparison
# ---------------------------------------------------------------------------
STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will "
    "would shall should may might can could of in to for with on at by from "
    "as into through during before after above below between out off over "
    "under again further then once here there when where why how all each "
    "every both few more most other some such no nor not only own same so "
    "than too very and but or if while that this these those it its he she "
    "they them their what which who whom your you i me my we us our about "
    "up also just don re ve ll s t d m how-to guide best free complete "
    "top new get make need know".split()
)


def tokenize(text):
    """Lowercase, strip non-alpha, remove stop words, min length 3."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) >= TAG_TOKEN_MIN_LEN]


# ---------------------------------------------------------------------------
# Parse posts
# ---------------------------------------------------------------------------
def parse_post(filepath):
    """Extract front matter + first 100 words of body from a markdown post."""
    raw = filepath.read_text(encoding="utf-8", errors="replace")

    # Split front matter
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None

    title = fm.get("title", "")
    categories = fm.get("categories", [])
    if isinstance(categories, str):
        categories = [categories]
    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    image = fm.get("image", "")

    # Body: strip HTML/markdown markup, take first 100 words
    body = parts[2]
    body = re.sub(r"<[^>]+>", " ", body)          # strip HTML
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)  # strip images
    body = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", body)    # strip links
    body = re.sub(r"[#*_>`~|]", " ", body)         # strip markdown chars
    words = body.split()[:100]
    first_100 = " ".join(words)

    # Build slug from filename: 2025-10-27-my-post.md -> my-post
    stem = filepath.stem  # e.g. 2025-10-27-my-post
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)

    # Build URL path from filename per permalink /:year/:month/:day/:title/
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})-(.+)", filepath.stem)
    if m:
        url = f"/{m.group(1)}/{m.group(2)}/{m.group(3)}/{m.group(4)}/"
    else:
        url = f"/{slug}/"

    return {
        "slug": slug,
        "filepath": str(filepath.name),
        "title": title,
        "category": categories[0].lower() if categories else "",
        "tags": [t.lower() for t in tags],
        "tag_tokens": _tag_to_tokens(tags),
        "title_tokens": tokenize(title),
        "content_tokens": tokenize(first_100),
        "image": image,
        "url": url,
    }


def _tag_to_tokens(tags):
    """Flatten all tags into individual tokens for partial matching."""
    tokens = set()
    for tag in tags:
        for t in re.findall(r"[a-z0-9]+", tag.lower()):
            if len(t) >= TAG_TOKEN_MIN_LEN:
                tokens.add(t)
    return tokens


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def tag_pair_score(tags_a, tags_b, tokens_a, tokens_b):
    """
    Score tag similarity between two posts using tiered matching:
      1. Exact tag match          -> 1.0 per pair
      2. Substring containment    -> 0.6 per pair
      3. Token overlap            -> proportional
    Returns a score normalized to [0, 1].
    """
    if not tags_a and not tags_b:
        return 0.0

    set_a = set(tags_a)
    set_b = set(tags_b)

    # Tier 1: exact matches
    exact = set_a & set_b
    exact_score = len(exact) * TAG_EXACT_SCORE

    # Tier 2: substring containment (excluding already-matched exact pairs)
    remaining_a = set_a - exact
    remaining_b = set_b - exact
    substring_count = 0
    for ta in remaining_a:
        for tb in remaining_b:
            if ta in tb or tb in ta:
                substring_count += 1
    substring_score = substring_count * TAG_SUBSTRING_SCORE

    # Tier 3: token overlap
    if tokens_a and tokens_b:
        shared = tokens_a & tokens_b
        total = tokens_a | tokens_b
        token_ratio = len(shared) / len(total) if total else 0
    else:
        token_ratio = 0

    # Combine: normalize by total unique tags across both posts
    all_tags = set_a | set_b
    max_possible = len(all_tags) * TAG_EXACT_SCORE if all_tags else 1
    raw = exact_score + substring_score + (token_ratio * max_possible * 0.3)
    return min(raw / max_possible, 1.0)


def jaccard(set_a, set_b):
    """Jaccard similarity for two token sets."""
    if not set_a and not set_b:
        return 0.0
    inter = set_a & set_b
    union = set_a | set_b
    return len(inter) / len(union)


def score_pair(post_a, post_b):
    """Compute composite similarity score between two posts."""
    # Category: binary
    cat_score = 1.0 if (post_a["category"] and
                        post_a["category"] == post_b["category"]) else 0.0

    # Tags: tiered partial matching
    tag_score = tag_pair_score(
        post_a["tags"], post_b["tags"],
        post_a["tag_tokens"], post_b["tag_tokens"]
    )

    # Title: token Jaccard
    title_score = jaccard(
        set(post_a["title_tokens"]),
        set(post_b["title_tokens"])
    )

    # Content (first 100 words): token Jaccard
    content_score = jaccard(
        set(post_a["content_tokens"]),
        set(post_b["content_tokens"])
    )

    return (W_CATEGORY * cat_score +
            W_TAGS     * tag_score +
            W_TITLE    * title_score +
            W_CONTENT  * content_score)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main():
    # Resolve paths
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent
    posts_dir = root / "_posts"
    data_dir = root / "_data"
    data_dir.mkdir(exist_ok=True)

    # Parse all posts
    md_files = sorted(posts_dir.glob("*.md"))
    posts = []
    for f in md_files:
        p = parse_post(f)
        if p:
            posts.append(p)

    print(f"[related-posts] Parsed {len(posts)} posts")

    if len(posts) < 2:
        print("[related-posts] Not enough posts to generate relations.")
        sys.exit(0)

    # Build slug -> index lookup
    slug_idx = {p["slug"]: i for i, p in enumerate(posts)}

    # Compute all pairwise scores
    n = len(posts)
    scores = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            s = score_pair(posts[i], posts[j])
            scores[i][j] = s
            scores[j][i] = s

    # For each post, rank candidates by score descending
    ranked = []
    for i in range(n):
        candidates = sorted(
            [(j, scores[i][j]) for j in range(n) if j != i],
            key=lambda x: -x[1]
        )
        ranked.append(candidates)

    # --------------- Assignment with inbound cap + orphan prevention --------
    # Phase 1: assign top NUM_RELATED for each post, respecting inbound cap
    inbound_count = defaultdict(int)
    assignments = [[] for _ in range(n)]

    for i in range(n):
        for j, sc in ranked[i]:
            if len(assignments[i]) >= NUM_RELATED:
                break
            if inbound_count[j] < INBOUND_CAP:
                assignments[i].append(j)
                inbound_count[j] += 1

    # Phase 2: fill any post that got fewer than NUM_RELATED (cap was tight)
    for i in range(n):
        if len(assignments[i]) < NUM_RELATED:
            for j, sc in ranked[i]:
                if j not in assignments[i]:
                    assignments[i].append(j)
                    inbound_count[j] += 1
                    if len(assignments[i]) >= NUM_RELATED:
                        break

    # Phase 3: orphan prevention - every post must appear in at least one
    # other post's related list
    assigned_set = set()
    for asn in assignments:
        assigned_set.update(asn)

    orphans = [i for i in range(n) if i not in assigned_set]
    print(f"[related-posts] Orphans before fix: {len(orphans)}")

    for orphan in orphans:
        # Find the post that scores highest against this orphan
        best_host = None
        best_score = -1
        for i in range(n):
            if i == orphan:
                continue
            if scores[i][orphan] > best_score:
                best_score = scores[i][orphan]
                best_host = i
        if best_host is not None:
            assignments[best_host].append(orphan)
            inbound_count[orphan] += 1

    # Verify no orphans remain
    assigned_set.clear()
    for asn in assignments:
        assigned_set.update(asn)
    remaining_orphans = [i for i in range(n) if i not in assigned_set]
    print(f"[related-posts] Orphans after fix: {len(remaining_orphans)}")

    # --------------- Write YAML output -------------------------------------
    output = {}
    for i in range(n):
        slug = posts[i]["slug"]
        related_list = []
        for j in assignments[i]:
            related_list.append({
                "slug": posts[j]["slug"],
                "title": posts[j]["title"],
                "url": posts[j]["url"],
                "category": posts[j]["category"],
                "image": posts[j]["image"],
            })
        output[slug] = related_list

    out_path = data_dir / "related_posts.yml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True,
                  width=200, sort_keys=False)

    print(f"[related-posts] Wrote {out_path} with {len(output)} entries")

    # Quick stats
    inbound_vals = list(inbound_count.values())
    if inbound_vals:
        print(f"[related-posts] Inbound links - min: {min(inbound_vals)}, "
              f"max: {max(inbound_vals)}, "
              f"avg: {sum(inbound_vals)/len(inbound_vals):.1f}")


if __name__ == "__main__":
    main()
