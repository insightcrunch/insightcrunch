#!/usr/bin/env python3
"""
assign_blog_images.py
---------------------
Distributes blog images from assets/images/blog/ across all posts.

What it does:
  1. REPLACES existing placeholder images with hash-based assignments
     (both frontmatter image: field and inline markdown images)
  2. ADDS image: to frontmatter if missing entirely
  3. ADDS inline markdown image to body if no blog image exists in body
     (placed after <!--more--> if present, else after first paragraph)
  4. Deduplicates multiple body images (keeps first, removes rest)

Deterministic: same post always gets same image for a given pool size.
Idempotent: safe to re-run any number of times.

Usage:
  python3 _scripts/assign_blog_images.py
  python3 _scripts/assign_blog_images.py --dry-run
"""

import hashlib
import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO_ROOT, "_posts")
IMAGES_DIR = os.path.join(REPO_ROOT, "assets", "images", "blog")

OLD_PLACEHOLDER = "technology-industry-analysis-insightcrunch.webp"

BLOG_IMG_RE = re.compile(r'^!\[[^\]]*\]\(/assets/images/blog/[^\s)]+\.webp\)\s*$')
CAPTION_RE = re.compile(
    r'^(?:\*[^*]+\*|[A-Z\u0080-\uffff][^.!?\n]{3,115})$'
)


def get_image_pool():
    pattern = os.path.join(IMAGES_DIR, "*.webp")
    files = sorted([os.path.basename(f) for f in glob.glob(pattern)])
    if not files:
        print("ERROR: No .webp files found in assets/images/blog/")
        sys.exit(1)
    return files


def pick_image(post_filename, pool):
    h = hashlib.md5(post_filename.encode()).hexdigest()
    idx = int(h, 16) % len(pool)
    return pool[idx]


def get_title_from_frontmatter(content):
    """Extract title from frontmatter for alt text."""
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "Insight Crunch"


def has_frontmatter_image(content):
    """Check if frontmatter has an image: field with a value."""
    fm_match = re.match(r'^---\s*\n([\s\S]*?)\n---', content)
    if not fm_match:
        return False
    fm = fm_match.group(1)
    return bool(re.search(r'^image:\s*["\']?/\S+', fm, re.MULTILINE))


def has_body_blog_image(content):
    """Check if body contains any inline blog image."""
    fm_match = re.match(r'^---\s*\n[\s\S]*?\n---\s*\n', content)
    body = content[fm_match.end():] if fm_match else content
    return bool(re.search(r'!\[[^\]]*\]\(/assets/images/blog/[^\s)]+\.webp\)', body))


def add_frontmatter_image(content, new_path):
    """Add image: field to frontmatter if missing."""
    # Insert before the closing ---
    m = re.match(r'^(---\s*\n[\s\S]*?)\n(---\s*\n)', content)
    if m:
        return m.group(1) + f'\nimage: "{new_path}"\n' + m.group(2) + content[m.end():]
    return content


def add_body_image(content, new_path, title):
    """Add inline markdown image to body after <!--more--> or first paragraph."""
    alt_text = f"{title} - Insight Crunch"
    img_line = f"\n![{alt_text}]({new_path})\n"

    fm_match = re.match(r'^(---\s*\n[\s\S]*?\n---\s*\n)', content)
    if not fm_match:
        return content

    front = fm_match.group(1)
    body = content[fm_match.end():]

    # Strategy 1: insert after <!--more-->
    more_match = re.search(r'(<!--more-->)\s*\n', body)
    if more_match:
        insert_pos = more_match.end()
        body = body[:insert_pos] + img_line + body[insert_pos:]
        return front + body

    # Strategy 2: insert after first paragraph (first blank line)
    blank_match = re.search(r'\n\n', body)
    if blank_match:
        insert_pos = blank_match.end()
        body = body[:insert_pos] + img_line.lstrip('\n') + "\n" + body[insert_pos:]
        return front + body

    # Fallback: prepend to body
    return front + img_line + body


def is_caption(line):
    s = line.strip()
    if not s or len(s) > 120:
        return False
    if s.startswith(('#', '-', '*   ', '1.', '>', '[', '|', '---', '```', '<')):
        return False
    if s.startswith('*') and s.endswith('*') and len(s) > 2:
        return True
    if len(s) < 120 and s.count('. ') <= 1:
        return True
    return False


def dedupe_body_images(content):
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
                first_found = True
                new_lines.append(line)
                i += 1
            else:
                i += 1
                if i < len(lines) and lines[i].strip() != '' and is_caption(lines[i]):
                    i += 1
        else:
            new_lines.append(line)
            i += 1

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


def process_post(filepath, image_filename, dry_run=False):
    """Full pipeline: replace placeholders, add missing, dedupe."""
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    new_path = f"/assets/images/blog/{image_filename}"
    content = original
    title = get_title_from_frontmatter(content)
    actions = []

    # --- 1. Replace existing placeholder references ---
    img_re_part = r'(?:blog/[^\s"\')\]]+\.webp|' + re.escape(OLD_PLACEHOLDER) + r')'

    fm_pattern = re.compile(
        r'''^(image:\s*['"])(/assets/images/''' + img_re_part + r''')(['"])''',
        re.MULTILINE
    )
    content, n1 = fm_pattern.subn(rf'\g<1>{new_path}\3', content)

    inline_pattern = re.compile(
        r'(!\[[^\]]*\]\()(/assets/images/' + img_re_part + r')(\))'
    )
    content, n2 = inline_pattern.subn(rf'\g<1>{new_path}\3', content)

    url_pattern = re.compile(
        r'(url\()(/assets/images/' + img_re_part + r')(\))'
    )
    content, n3 = url_pattern.subn(rf'\g<1>{new_path}\3', content)

    if n1 + n2 + n3 > 0:
        actions.append(f"replaced {n1+n3} fm + {n2} inline")

    # --- 2. Add frontmatter image if missing ---
    if not has_frontmatter_image(content):
        content = add_frontmatter_image(content, new_path)
        actions.append("added fm image")

    # --- 3. Add body image if missing ---
    if not has_body_blog_image(content):
        content = add_body_image(content, new_path, title)
        actions.append("added body image")

    # --- 4. Dedupe body images ---
    content = dedupe_body_images(content)

    modified = content != original

    if modified and not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return modified, actions


def main():
    dry_run = "--dry-run" in sys.argv

    pool = get_image_pool()
    print(f"Image pool: {len(pool)} images in assets/images/blog/")
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

        was_modified, actions = process_post(post_path, assigned, dry_run)

        if was_modified:
            updated += 1
            prefix = "[DRY] " if dry_run else ""
            print(f"  {prefix}{post_filename} -> {assigned} ({', '.join(actions)})")
        else:
            skipped += 1

    print()
    action = "Would update" if dry_run else "Updated"
    print(f"{action}: {updated} posts")
    print(f"Already correct: {skipped}")
    print()
    print("Distribution across images:")
    for img, count in sorted(distribution.items()):
        bar = "#" * count
        print(f"  {img}: {count:3d} {bar}")


if __name__ == "__main__":
    main()
