# InsightCrunch Admin - Encryption & Maintenance Guide

## Architecture

All admin pages are encrypted with [StatiCrypt](https://github.com/robinmoisson/staticrypt). The dashboard (`index.html`) loads other pages in an iframe. A single login unlocks all tabs because every file shares the same salt and localStorage keys.

### Files

| File | Type | Description |
|------|------|-------------|
| `index.html` | Encrypted | Dashboard shell with sidebar navigation |
| `posts.html` | Encrypted | Posts dashboard (table, search, SEO scores) |
| `scheduled.html` | Encrypted | Scheduled posts viewer (GitHub API) |
| `doctor.html` | Encrypted | Posts Doctor (quality audit, issue detection) |
| `article-ideas.html` | Encrypted | AI article idea generator |
| `link-inspector.html` | Encrypted | Link Inspector (cross-linking diagnostics) |
| `keyword-audit.html` | Encrypted | Keyword Audit (slug/title vs body gap detection) |
| `keyword-audit-data.json` | Generated | Output of `_scripts/keyword_audit.py`, refreshed on scheduled builds |
| `posts-data.json` | Jekyll template | Generates JSON of all posts at build time |
| `related-data.json` | Jekyll template | Generates JSON of related posts data at build time |
| `ic-password-template.html` | Template | Custom StatiCrypt password prompt UI |
| `README.md` | Docs | This file |

### Critical: Shared Salt

All encrypted files MUST use the same salt for single-sign-on to work:

```
0225b0a7b3aac02f31e146d7af8711cb
```

If files are encrypted with different salts, each iframe tab will prompt for the password again individually.

### localStorage Keys (shared across all pages)

```
rememberExpirationKey: "staticrypt_expiration"
rememberPassphraseKey: "staticrypt_passphrase"
rememberDurationInDays: 30
```

---

## Workflow: Fixing an Encrypted Page

When asking Claude to fix a bug or add a feature in any admin page, start the conversation with:

> Read `admin/README.md` first, then proceed with the fix.

### Step-by-step (what Claude should do)

1. **Read this README** to know the salt, template path, and file relationships.

2. **Decrypt the target file** using the password the user provides and the 3-step PBKDF2 process StatiCrypt uses:
   - Round 1: PBKDF2(password, salt, 1000 iterations, SHA-1)
   - Round 2: PBKDF2(round1_hex, salt, 14000 iterations, SHA-256)
   - Round 3: PBKDF2(round2_hex, salt, 585000 iterations, SHA-256)
   - Salt is UTF-8 encoded (not hex-decoded) when passed to PBKDF2
   - Signed message format: first 64 hex chars = HMAC, rest = encrypted
   - Encrypted format: first 32 hex chars = IV (16 bytes), rest = AES-CBC ciphertext

3. **Apply fixes** to the decrypted inner HTML.

4. **Re-encrypt** using StatiCrypt CLI with the shared salt:

```bash
npx staticrypt <inner-file>.html \
  -p <password> \
  -s 0225b0a7b3aac02f31e146d7af8711cb \
  -t admin/ic-password-template.html \
  -d output \
  --remember 30 \
  --template-title "Admin Area" \
  --template-button UNLOCK \
  --template-placeholder "Enter password" \
  --template-error "Incorrect password. Please try again." \
  --template-instructions "Enter the admin password to access this page." \
  --short \
  -c false
```

5. **Verify** the salt in the output matches `0225b0a7b3aac02f31e146d7af8711cb`.

6. **Verify** round-trip decryption works before delivering files.

---

## Workflow: Adding a New Admin Page

1. Build the inner HTML page (no encryption, standalone).
2. Add a sidebar link in `dashboard-inner.html` under the appropriate section, with an SVG icon and `data-page="newpage.html"`.
3. Optionally add a welcome card in the welcome screen section.
4. Encrypt BOTH the new page AND the updated dashboard with the shared salt (see command above).
5. Deliver: new encrypted page + updated `index.html`.

---

## posts-data.json Notes

This is a Jekyll/Liquid template that generates JSON at build time. It iterates `site.posts` and outputs metadata for each post.

**Performance warning:** Avoid using `{{ post.content | size }}` or any filter that forces full markdown-to-HTML rendering of every post's body. With 500+ posts, this hits GitHub Pages' Liquid processing limits and silently truncates the JSON output. Stick to lightweight fields like `number_of_words`, `title | size`, `excerpt | strip_html | size`, etc.

---

## Scheduled Posts Page Notes

`scheduled.html` uses the public GitHub API to list files in `_posts/` and filters for future-dated filenames. For each future file, it fetches the raw markdown from `raw.githubusercontent.com` to parse YAML frontmatter (title, categories, tags, image, excerpt) and count words from the body. This is needed because `_config.yml` has `future: false`, so Jekyll excludes future posts from all Liquid loops including `posts-data.json`. No API key is needed since the repo is public.

---

## Posts Doctor Page Notes

`doctor.html` loads from the same `posts-data.json` as the Posts Dashboard. It runs quality diagnostics on every post and shows only those with issues. Checks include: missing featured image, missing excerpt, no tags, thin content (<300 words), short content (<600 words), title too long/short, slug too long, and poor SEO score (<50). Each issue is classified as critical or warning. Filters allow drilling down by issue type, category, and sort order.

---

## Link Inspector Page Notes

`link-inspector.html` loads from `related-data.json` (generated at build time from `_data/related_posts.yml`) and `posts-data.json`. It provides cross-linking diagnostics across six tabs: Overview (histogram, top/bottom linked posts), Inbound Links (searchable/filterable table), Outbound Links (with cross-category count), Orphan Check (zero-inbound detection), Category Clusters (intra vs inter linking stats), and Weakest Links (posts with fewest total connections). Requires the `_scripts/generate_related_posts.py` pre-build step to populate `_data/related_posts.yml`.

---

## Keyword Audit Page Notes

`keyword-audit.html` loads from `keyword-audit-data.json` (generated by `_scripts/keyword_audit.py`). It detects posts where proper nouns (cities, companies, technologies, exams, programs) in the URL slug or title are missing from the `page_title` field and/or post body. This catches SEO gaps where a user clicks through expecting content about a specific topic (e.g. "TCS ILP Bhubaneswar") but the body never mentions that keyword.

Issue types detected:
- **SLUG_KEYWORD_MISSING_FROM_BODY** (critical): Proper noun in slug, zero body mentions
- **SLUG_KEYWORD_SPARSE_IN_BODY** (warning): Proper noun in slug, fewer than 3 mentions in 2000+ word post
- **TITLE_KEYWORD_MISSING_FROM_BODY** (critical): Proper noun in title, zero body mentions
- **TITLE_KEYWORD_SPARSE_IN_BODY** (warning): Proper noun in title, fewer than 3 mentions in 2000+ word post
- **MISSING_FROM_PAGE_TITLE** (critical): Proper noun in title but absent from page_title
- **NO_PAGE_TITLE** (warning): Post has no page_title field at all

The audit runs during scheduled and manual builds (`_scripts/keyword_audit.py`) and commits `admin/keyword-audit-data.json` alongside other automated post updates. The known-noun dictionary in the script can be expanded as new proper nouns become relevant.

### Dashboard Sidebar Entry

Add this to the sidebar in `index.html` (decrypted inner HTML) alongside the other nav items, using the appropriate `data-page` attribute:

```html
<a data-page="link-inspector.html">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512"><path d="M579.8 267.7c56.5-56.5 56.5-148 0-204.5c-50-50-128.8-56.5-186.3-15.4l-1.6 1.1c-14.4 10.3-17.7 30.3-7.4 44.6s30.3 17.7 44.6 7.4l1.6-1.1c32.1-22.9 76-19.3 103.8 8.6c31.5 31.5 31.5 82.5 0 114L422.3 334.8c-31.5 31.5-82.5 31.5-114 0c-27.9-27.9-31.5-71.8-8.6-103.8l1.1-1.6c10.3-14.4 6.9-34.4-7.4-44.6s-34.4-6.9-44.6 7.4l-1.1 1.6C206.5 251.2 213 330 263 380c56.5 56.5 148 56.5 204.5 0L579.8 267.7zM60.2 244.3c-56.5 56.5-56.5 148 0 204.5c50 50 128.8 56.5 186.3 15.4l1.6-1.1c14.4-10.3 17.7-30.3 7.4-44.6s-30.3-17.7-44.6-7.4l-1.6 1.1c-32.1 22.9-76 19.3-103.8-8.6C74 372.1 74 321.1 105.5 289.5L217.7 177.2c31.5-31.5 82.5-31.5 114 0c27.9 27.9 31.5 71.8 8.6 103.8l-1.1 1.6c-10.3 14.4-6.9 34.4 7.4 44.6s34.4 6.9 44.6-7.4l1.1 1.6C433.5 260.8 427 182 377 132c-56.5-56.5-148-56.5-204.5 0L60.2 244.3z"/></svg>
  Link Inspector
</a>
```

After adding the sidebar entry, encrypt both `link-inspector.html` and the updated `index.html` using the shared salt.

---

## Quick Reference

| Item | Value |
|------|-------|
| Shared salt | `0225b0a7b3aac02f31e146d7af8711cb` |
| localStorage expiration key | `staticrypt_expiration` |
| localStorage passphrase key | `staticrypt_passphrase` |
| Remember duration | 30 days |
| Password template | `ic-password-template.html` |
| PBKDF2 total iterations | 600,000 (1k + 14k + 585k) |
| GitHub repo | `insightcrunch/insightcrunch` |
| Jekyll future posts | Disabled (`future: false`) |

---

## Fast-Track Workflow for Claude

> **Purpose:** This section eliminates the discovery overhead Claude faces when modifying admin pages. Read this FIRST, skip all exploratory steps, and go straight to execution.

### One-Command Decrypt

```bash
cd admin
npx staticrypt --decrypt -p 7777 -s 0225b0a7b3aac02f31e146d7af8711cb --short -d decrypted -c false TARGET.html
```

Replace `TARGET.html` with one or more filenames. The decrypted inner HTML lands in `admin/decrypted/TARGET.html`.

### One-Command Encrypt

```bash
npx staticrypt INNER.html \
  -p 7777 \
  -s 0225b0a7b3aac02f31e146d7af8711cb \
  -t admin/ic-password-template.html \
  -d output \
  --remember 30 \
  --template-title "Admin Area" \
  --template-button UNLOCK \
  --template-placeholder "Enter password" \
  --template-error "Incorrect password. Please try again." \
  --template-instructions "Enter the admin password to access this page." \
  --short \
  -c false
```

Multiple files can be passed in one call. Output lands in `output/INNER.html`.

### Verify (mandatory before delivery)

```bash
# 1. Salt present
grep -c '0225b0a7b3aac02f31e146d7af8711cb' output/TARGET.html
# Must print 1

# 2. Round-trip
npx staticrypt --decrypt -p 7777 -s 0225b0a7b3aac02f31e146d7af8711cb --short -d verify -c false output/TARGET.html
head -5 verify/TARGET.html
# Must show <!DOCTYPE html> (the real inner HTML, not the staticrypt wrapper)
```

### Step-by-Step: Modify an Existing Page

1. `npm install -g staticrypt` (once per session)
2. Decrypt the target: `npx staticrypt --decrypt ... TARGET.html`
3. Apply edits to `decrypted/TARGET.html`
4. Re-encrypt: `npx staticrypt decrypted/TARGET.html ...`
5. Verify salt + round-trip
6. Rename/copy `output/TARGET.html` to final delivery name
7. Deliver

### Step-by-Step: Add a New Page

1. Build the inner HTML as a standalone file (no encryption, no staticrypt wrapper)
2. Decrypt `index.html` (the dashboard)
3. In decrypted `index.html`, add:
   - A sidebar `<li>` with `data-page="newpage.html"` and an SVG icon under the appropriate `sidebar-section`
   - A welcome card `<a class="wcard">` in the `welcome-grid` div
4. Encrypt BOTH the new page AND the updated `index.html` with the shared salt
5. Verify salt + round-trip for both
6. Deliver: new encrypted page + updated `index.html`

### Dashboard Anatomy (decrypted index.html)

```
<div class="sidebar">
  <div class="sidebar-section">
    <div class="sidebar-section-label">Content</div>
    <ul class="sidebar-nav">
      <!-- Each tool: <li><a href="#" data-page="FILENAME" onclick="loadPage(this, event)">ICON LABEL</a></li> -->
    </ul>
  </div>
  <div class="sidebar-section">
    <div class="sidebar-section-label">Tools</div>
    <ul class="sidebar-nav">
      <!-- External links like GitHub -->
    </ul>
  </div>
</div>

<div class="welcome-grid">
  <!-- Each card: <a class="wcard" href="#" onclick="loadPageByName('FILENAME', event)">...</a> -->
</div>
```

### Style Reference (all pages must match)

```css
/* Core palette */
--bg:#0f0b08; --bg2:#1a1410; --bg3:#241c14; --bg4:#2e2418;
--ink:#e8dfd0; --mid:#a89878; --soft:#786850; --faint:#3e3428;
--amber:#d08020; --amber-dim:#805010; --amber-bg:rgba(208,128,32,.08);
--green:#48a848; --red:#d04040; --yellow:#c8a020; --blue:#4888d0;

/* Fonts */
font-family: 'Inter', sans-serif;          /* body */
font-family: 'Lora', serif;               /* headings, quotes */
Google Fonts import: Lora (400,500,600,italic) + Inter (300-700)

/* Component patterns */
.stat-card     -> stats row
.toolbar       -> search + filter bar
.tbl-wrap      -> table container
.tbl-footer    -> pagination
.loading-screen -> spinner on load
.admin-wrap    -> max-width:1500px centered
```

### Data Sources (all tools load from these)

| File | Contents | Generated By |
|------|----------|-------------|
| `posts-data.json` | All published posts metadata | Jekyll build (Liquid template) |
| `authors-data.json` | Author pool definitions | Jekyll build |
| `related-data.json` | Related posts graph | `_scripts/generate_related_posts.py` |
| `links-data.json` | External links cache | `_scripts/extract_links.py` |
| `keyword-audit-data.json` | Keyword gap data | `_scripts/keyword_audit.py` |

### Hub-Spoke Pipeline Data

The `POOL_HUBS` variable (present in both `author-map.html` and `pipeline.html`) defines the content plan. When adding new article series, add spokes to the appropriate pool key. Both files must stay in sync. Current pools with hubs:

| Pool Key | Hubs |
|----------|------|
| `south-asian-it` | TCS Career, TCS ILP, NQT, IT Comparison |
| `south-asian-exam` | UPSC Overview, Prelims, Mains, Optional, Interview, Comparisons, Topic Guides, CAT |
| `south-asian-ent` | Bollywood Franchise, Indian Culture |
| `east-asian` | Gaokao Subjects, University Admissions, Gaokao Reform |
| `western-lit` | HP Characters (x4), HP Themes (x2), HP Comparisons, Lit Classics (x7) |
| `western-edu` | SAT Math (x2), SAT Reading, SAT Writing, SAT Score, SAT Planning, SAT University |
| `western-tech` | AI Deep Dives, Anthropic, Claude Dev, Anthropic Careers, AI Benchmarks |
| Others | ENEM, Suneung, Kyotsu, EGE, JAMB, UK, CPNS, Baccalaureat |

### Flags to Remember

| Flag | Why |
|------|-----|
| `--short` | Suppresses the "password too short" interactive prompt (our password is 4 chars) |
| `-c false` | Disables config file creation (prevents `.staticrypt.json` from being written) |
| `-s SALT` | Must always pass the shared salt explicitly |
| `--remember 30` | Sets localStorage remember-me to 30 days |
