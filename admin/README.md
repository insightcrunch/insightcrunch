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
| `posts-data.json` | Jekyll template | Generates JSON of all posts at build time |
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
