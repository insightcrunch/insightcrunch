#!/usr/bin/env python3
"""
assign_blog_images.py
---------------------
Distributes blog images from assets/images/blog/ across all posts
that currently use the default placeholder image.

How it works:
  - Scans assets/images/blog/ for all .webp files (sorted for stability)
  - For each post in _posts/, hashes the filename to pick an image
  - Updates both:
      1. Front matter  image: "/assets/images/blog/blog-XX.webp"
      2. Inline markdown  ![alt text](/assets/images/blog/blog-XX.webp)
  - Preserves alt text in inline images

Scalable:
  - Add more .webp files to assets/images/blog/, re-run, and posts
    automatically redistribute across the expanded pool.
  - Deterministic: same post always gets same image for a given pool size.
  - Idempotent: safe to re-run any number of times.

Usage:
  cd insightcrunch-main
  python3 _scripts/assign_blog_images.py
  python3 _scripts/assign_blog_images.py --dry-run   # preview only
"""

import hashlib
import glob
import os
import re
import sys

# ---------- config ----------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO_ROOT, "_posts")
IMAGES_DIR = os.path.join(REPO_ROOT, "assets", "images", "blog")

# The old default placeholder (what we're replacing FROM)
OLD_PLACEHOLDER = "technology-industry-analysis-insightcrunch.webp"

# ---------- helpers ----------

def get_image_pool():
    """Return sorted list of image filenames in the blog images folder."""
    pattern = os.path.join(IMAGES_DIR, "*.webp")
    files = sorted([os.path.basename(f) for f in glob.glob(pattern)])
    if not files:
        print("ERROR: No .webp files found in assets/images/blog/")
        sys.exit(1)
    return files


def pick_image(post_filename, pool):
    """Deterministically pick an image for a post using its filename hash."""
    h = hashlib.md5(post_filename.encode()).hexdigest()
    idx = int(h, 16) % len(pool)
    return pool[idx]


def process_post(filepath, image_filename, dry_run=False):
    """Replace placeholder image references and dedupe body images."""
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    new_path = f"/assets/images/blog/{image_filename}"
    content = original
    # Matches any .webp inside blog/ OR the old root-level placeholder
    img_re_part = r'(?:blog/[^\s"\')\]]+\.webp|' + re.escape(OLD_PLACEHOLDER) + r')'

    # --- 1. Front matter image: field (double or single quoted) ---
    fm_pattern = re.compile(
        r'''^(image:\s*['"])(/assets/images/''' + img_re_part + r''')(['"])''',
        re.MULTILINE
    )
    content, n1 = fm_pattern.subn(rf'\g<1>{new_path}\3', content)

    # --- 2. Inline markdown images ---
    inline_pattern = re.compile(
        r'(!\[[^\]]*\]\()(/assets/images/' + img_re_part + r')(\))'
    )
    content, n2 = inline_pattern.subn(rf'\g<1>{new_path}\3', content)

    # --- 3. CSS/JS url() references ---
    url_pattern = re.compile(
        r'(url\()(/assets/images/' + img_re_part + r')(\))'
    )
    content, n3 = url_pattern.subn(rf'\g<1>{new_path}\3', content)

    # --- 4. Dedupe body images: keep first, remove rest + captions ---
    content = dedupe_body_images(content)

    # Only write if content actually changed (true idempotency)
    modified = content != original

    if modified and not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return modified, n1 + n3, n2


# Blog image pattern for body deduplication
BLOG_IMG_RE = re.compile(r'^!\[[^\]]*\]\(/assets/images/blog/[^\s)]+\.webp\)\s*$')

# Caption pattern: short line (< 120 chars), not blank, not a heading,
# not a list item, not a link, not a horizontal rule, not starting a paragraph
# that's clearly long-form content. Includes *italic* captions.
CAPTION_RE = re.compile(
    r'^(?:\*[^*]+\*|[A-Z\u0080-\uffff][^.!?\n]{3,115})$'
)


def is_caption(line):
    """Return True if line looks like a short image caption."""
    s = line.strip()
    if not s or len(s) > 120:
        return False
    # Definitely not a caption
    if s.startswith(('#', '-', '*   ', '1.', '>', '[', '|', '---', '```', '<')):
        return False
    # Italic captions like *Chinese text here*
    if s.startswith('*') and s.endswith('*') and len(s) > 2:
        return True
    # Short text caption (< 120 chars, no period-heavy sentences typical of paragraphs)
    if len(s) < 120 and s.count('. ') <= 1:
        return True
    return False


def dedupe_body_images(content):
    """Keep only the first blog image in the body, remove duplicates + captions."""
    # Split front matter from body
    fm_match = re.match(r'^(---\s*\n.*?\n---\s*\n)', content, re.DOTALL)
    if not fm_match:
        return content

    front_matter = fm_match.group(1)
    body = content[fm_match.end():]
    lines = body.split('\n')

    first_found = False
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if BLOG_IMG_RE.match(line + '\n') or BLOG_IMG_RE.match(line):
            if not first_found:
                # Keep the first image
                first_found = True
                new_lines.append(line)
                i += 1
            else:
                # Skip this duplicate image
                i += 1
                # Check IMMEDIATE next line for caption (no blank line gap)
                if i < len(lines) and lines[i].strip() != '' and is_caption(lines[i]):
                    i += 1  # skip caption
        else:
            new_lines.append(line)
            i += 1

    # Collapse 3+ consecutive blank lines to max 2
    cleaned = []
    blank_count = 0
    for line in new_lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                cleaned.append(line)
        else:
            blank_count = 0
            cleaned.append(line)

    return front_matter + '\n'.join(cleaned)


# ---------- main ----------

def main():
    dry_run = "--dry-run" in sys.argv

    pool = get_image_pool()
    print(f"Image pool: {len(pool)} images in assets/images/blog/")
    for img in pool:
        print(f"  - {img}")
    print()

    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    print(f"Posts found: {len(posts)}")
    print()

    updated = 0
    skipped = 0
    distribution = {img: 0 for img in pool}

    for post_path in posts:
        post_filename = os.path.basename(post_path)
        assigned = pick_image(post_filename, pool)
        distribution[assigned] += 1

        was_modified, fm_hits, inline_hits = process_post(post_path, assigned, dry_run)

        if was_modified:
            updated += 1
            if dry_run:
                print(f"  [DRY] {post_filename} -> {assigned} (fm:{fm_hits}, inline:{inline_hits})")
        else:
            skipped += 1

    print()
    action = "Would update" if dry_run else "Updated"
    print(f"{action}: {updated} posts")
    print(f"Already correct / no placeholder: {skipped}")
    print()
    print("Distribution across images:")
    for img, count in sorted(distribution.items()):
        bar = "#" * count
        print(f"  {img}: {count:3d} {bar}")


if __name__ == "__main__":
    main()
