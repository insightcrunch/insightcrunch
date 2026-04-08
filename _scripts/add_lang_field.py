#!/usr/bin/env python3
"""
add_lang_field.py

Walks _posts/ and adds a `lang:` field to the YAML frontmatter of any post
that doesn't already have one.

Detection logic:
  1. Script-based detection. Counts characters from each writing system
     (Latin, CJK, Bengali, Devanagari, Tamil, Telugu, Kannada, Malayalam,
     Arabic). Non-Latin scripts are unambiguous and return directly.
  2. Latin-alphabet discrimination. Because Latin script is shared across
     English, Portuguese, Spanish, French, German, and Italian, any
     Latin-dominant post runs through a second pass that counts
     language-specific stopwords and picks the winning language. Default
     fallback is "en" whenever no foreign language has a clear signal.
  3. Title → body fallback. Pass 1 prefers a pure-script title. Pass 2
     falls back to body-majority if the title is mixed or empty.

Idempotent: re-running does nothing on posts that already have `lang:`.
First run on CI will backfill all existing posts in a single commit.
"""

import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"

# ---------------------------------------------------------------------------
# Stage 1: script-based detection (unambiguous for non-Latin languages)
# ---------------------------------------------------------------------------
LANG_RANGES = [
    ("en", re.compile(r"[A-Za-zÀ-ÿ]")),                    # Latin (with diacritics)
    ("zh", re.compile(r"[\u4E00-\u9FFF\u3400-\u4DBF]")),   # CJK Unified
    ("bn", re.compile(r"[\u0980-\u09FF]")),                # Bengali
    ("hi", re.compile(r"[\u0900-\u097F]")),                # Devanagari (Hindi)
    ("ta", re.compile(r"[\u0B80-\u0BFF]")),                # Tamil
    ("te", re.compile(r"[\u0C00-\u0C7F]")),                # Telugu
    ("kn", re.compile(r"[\u0C80-\u0CFF]")),                # Kannada
    ("ml", re.compile(r"[\u0D00-\u0D7F]")),                # Malayalam
    ("ur", re.compile(r"[\u0600-\u06FF]")),                # Arabic script (Urdu)
]

# ---------------------------------------------------------------------------
# Stage 2: Latin-alphabet language discrimination by stopword frequency
#
# Each language has a distinctive set of ultra-common function words that
# appear in nearly every sentence. Counting these in a post's text and
# comparing the tallies gives us reliable discrimination across Latin
# languages without needing a third-party NLP library.
#
# Tuning note: the thresholds in discriminate_latin() are deliberately
# conservative. A Portuguese post needs at least 8 Portuguese stopword hits
# AND must beat English by at least 20% before we switch away from the "en"
# default. This avoids false positives on English articles that casually
# mention foreign words in quotes, examples, or product names.
# ---------------------------------------------------------------------------
LATIN_STOPWORDS = {
    "en": {
        "the", "of", "and", "to", "in", "is", "it", "that", "for", "was",
        "with", "as", "on", "are", "by", "be", "this", "which", "or", "from",
        "at", "not", "but", "have", "has", "had", "will", "can", "an",
        "their", "they", "been", "were", "would", "there", "its", "if",
        "one", "all", "we", "he", "she", "you",
    },
    "pt": {
        "de", "que", "não", "é", "o", "a", "os", "as", "um", "uma", "uns",
        "umas", "do", "da", "dos", "das", "no", "na", "nos", "nas", "para",
        "com", "por", "pelo", "pela", "se", "mas", "ou", "como", "mais",
        "muito", "já", "também", "quando", "onde", "porque", "isso", "esse",
        "essa", "este", "esta", "sua", "seu", "suas", "seus", "foi", "são",
        "ser", "está", "estão", "ele", "ela", "eles", "elas", "às", "ao",
        "aos", "à", "pelos", "pelas", "têm", "tem", "entre", "sobre",
    },
    "es": {
        "el", "la", "los", "las", "de", "que", "y", "en", "un", "una", "por",
        "para", "con", "no", "es", "se", "al", "lo", "como", "más", "pero",
        "sus", "le", "ya", "o", "este", "esta", "sí", "porque", "entre",
        "cuando", "muy", "sin", "sobre", "también", "me", "hasta", "hay",
        "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno",
        "ni", "contra", "ese", "eso", "del", "les",
    },
    "fr": {
        "le", "la", "les", "de", "que", "et", "est", "en", "un", "une",
        "des", "du", "pas", "pour", "avec", "sur", "par", "au", "ce", "ne",
        "se", "qui", "plus", "ou", "mais", "dans", "sont", "son", "sa",
        "ses", "leur", "nous", "vous", "ils", "elles", "cette", "cet",
        "ces", "ma", "mon", "mes", "ta", "ton", "tes", "notre", "votre",
        "aux", "été", "être",
    },
    "de": {
        "der", "die", "das", "und", "zu", "in", "ist", "den", "von", "mit",
        "sich", "auf", "für", "nicht", "ein", "eine", "als", "auch", "es",
        "an", "werden", "aus", "er", "hat", "dass", "sie", "nach", "wird",
        "bei", "einer", "um", "am", "sind", "noch", "wie", "einem", "über",
        "einen", "so", "zum", "war", "haben", "nur", "oder", "aber",
    },
    "it": {
        "il", "lo", "la", "i", "gli", "le", "di", "che", "è", "e", "un",
        "una", "in", "per", "non", "con", "su", "da", "del", "della",
        "dello", "delle", "dei", "degli", "al", "alla", "allo", "alle",
        "ai", "agli", "nel", "nella", "sul", "sulla", "come", "ma", "se",
        "più", "anche", "quando", "dove", "perché", "molto", "sono", "ho",
        "ha", "hanno", "era", "sua", "suo", "loro",
    },
    "id": {
        "yang", "dan", "di", "ini", "itu", "dari", "dengan", "untuk",
        "adalah", "dalam", "pada", "tidak", "atau", "akan", "karena",
        "bisa", "tetapi", "juga", "dapat", "sudah", "saja", "sebagai",
        "secara", "lebih", "seperti", "mereka", "kita", "anda", "saya",
        "dia", "kami", "kamu", "ke", "oleh", "telah", "masih", "agar",
        "supaya", "ketika", "sampai", "hingga", "sebelum", "setelah",
        "bahwa", "apa", "siapa", "mengapa", "bagaimana",
    },
}

TOKEN_RE = re.compile(r"[a-zà-ÿA-ZÀ-Ÿ][a-zà-ÿA-ZÀ-Ÿ'\-]*", re.UNICODE)

# Discrimination thresholds (tuned conservatively).
# A non-English candidate must pass ALL THREE checks to win:
#   (1) Absolute floor:  at least this many stopword hits (guards against
#       tiny posts or coincidental matches in short text).
#   (2) Density floor:   at least this percentage of tokens must be
#       stopwords (guards against noisy matches in mixed-language or
#       romanized-script posts like Hindi-in-Latin-letters).
#   (3) Lead over en:    winner must beat English by this ratio (guards
#       against English posts that happen to contain a few foreign words
#       in quotes, product names, or examples).
# Tuning reference: on the real InsightCrunch catalog, true Portuguese
# posts score pt=240-280 with en=6 (40x+ ratio, 33-36% density). A
# romanized-Hindi post scored es=32 with en=21 (1.5x ratio, 3.8% density)
# and correctly fails both the density and ratio checks below.
MIN_TOKENS_FOR_DISCRIMINATION = 20
MIN_HITS_FOR_NON_EN_WIN        = 8
MIN_DENSITY_FOR_NON_EN_WIN     = 0.05
MIN_RATIO_OVER_EN              = 2.0


def discriminate_latin(text: str) -> str:
    """
    Given Latin-alphabet text, return the best matching language code.
    Conservative: returns "en" unless a foreign language has clear signal
    across all three gate checks (hits, density, ratio).
    """
    tokens = [t.lower() for t in TOKEN_RE.findall(text)][:1500]
    total = len(tokens)
    if total < MIN_TOKENS_FOR_DISCRIMINATION:
        return "en"

    scores = {
        lang: sum(1 for t in tokens if t in words)
        for lang, words in LATIN_STOPWORDS.items()
    }

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_lang, top_score = ranked[0]

    # English winning is always fine (the default).
    if top_lang == "en":
        return "en"

    # Non-English candidate must pass all three gates.
    en_score = scores["en"]
    density = top_score / total
    beats_en = (en_score == 0) or (top_score >= en_score * MIN_RATIO_OVER_EN)

    if (top_score >= MIN_HITS_FOR_NON_EN_WIN
            and density >= MIN_DENSITY_FOR_NON_EN_WIN
            and beats_en):
        return top_lang
    return "en"


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)
TITLE_RE       = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.MULTILINE)
PAGE_TITLE_RE  = re.compile(r'^page_title:\s*"?(.*?)"?\s*$', re.MULTILINE)
LANG_RE        = re.compile(r'^lang:\s*\S+\s*$', re.MULTILINE)


def _count_scripts(text: str) -> dict:
    return {code: len(rx.findall(text)) for code, rx in LANG_RANGES}


def detect_lang(title: str, body: str) -> str:
    title_counts = _count_scripts(title)
    nonzero_in_title = [code for code, n in title_counts.items() if n > 0]

    # Pass 1: title with exactly one script present
    if len(nonzero_in_title) == 1:
        detected = nonzero_in_title[0]
    else:
        # Pass 2: mixed or empty title → body majority with title fallback
        body_counts = _count_scripts(body)
        body_total = sum(body_counts.values())
        title_total = sum(title_counts.values())

        if body_total < title_total:
            winner = max(title_counts.items(), key=lambda x: x[1])
            detected = winner[0] if winner[1] > 0 else "en"
        elif body_total == 0:
            detected = "en"
        else:
            detected = max(body_counts.items(), key=lambda x: x[1])[0]

    # Stage 2: Latin-alphabet discrimination.
    # If script detection says "Latin" (en), run stopword discrimination
    # to distinguish en/pt/es/fr/de/it from each other. Non-Latin languages
    # (zh, bn, hi, ta, te, kn, ml, ur) are returned directly since their
    # scripts are unambiguous.
    if detected == "en":
        # Use title + first 5000 chars of body for discrimination signal.
        return discriminate_latin(title + " " + body[:5000])
    return detected


def process_file(path: Path, retag: bool = False) -> str:
    """Returns 'skipped', 'unchanged', 'added:<lang>', 'retagged:<lang>', or 'no-frontmatter'.

    Normal mode (retag=False): idempotent. Skips posts that already have
    a lang field. Safe to run repeatedly from CI.

    Retag mode (retag=True): re-runs detection on ALL posts, including
    those that already have a lang field. If the new detection result
    differs from the current value, the field is updated and the file
    is rewritten. If it matches, the file is left alone. Use this once
    after updating the detector logic to backfill fixes.
    """
    raw = path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(raw)
    if not fm_match:
        return "no-frontmatter"

    frontmatter = fm_match.group(1)
    body = raw[fm_match.end():]

    existing_lang_match = LANG_RE.search(frontmatter)
    if existing_lang_match and not retag:
        return "skipped"

    # Prefer page_title (richer, SEO-optimized). Fall back to title if absent.
    page_title_match = PAGE_TITLE_RE.search(frontmatter)
    title_match      = TITLE_RE.search(frontmatter)
    if page_title_match:
        title_for_detection = page_title_match.group(1)
    elif title_match:
        title_for_detection = title_match.group(1)
    else:
        title_for_detection = ""

    lang = detect_lang(title_for_detection, body)

    if existing_lang_match:
        # Retag mode: check if we need to rewrite at all.
        current_lang = re.match(r'^lang:\s*(\S+)', existing_lang_match.group(0)).group(1)
        if current_lang == lang:
            return "unchanged"
        # Replace the existing lang line with the new value.
        new_frontmatter = LANG_RE.sub(f"lang: {lang}", frontmatter)
        new_raw = f"---\n{new_frontmatter}---\n" + body
        path.write_text(new_raw, encoding="utf-8")
        return f"retagged:{lang}"

    # Normal add path.
    new_frontmatter = frontmatter.rstrip() + f"\nlang: {lang}\n"
    new_raw = f"---\n{new_frontmatter}---\n" + body
    path.write_text(new_raw, encoding="utf-8")
    return f"added:{lang}"


def main() -> int:
    if not POSTS_DIR.is_dir():
        print(f"ERROR: {POSTS_DIR} not found", file=sys.stderr)
        return 1

    retag = "--retag" in sys.argv[1:]

    counts = {
        "skipped": 0, "unchanged": 0, "no-frontmatter": 0,
        "added:en": 0, "added:pt": 0, "added:es": 0, "added:fr": 0,
        "added:de": 0, "added:it": 0, "added:id": 0,
        "added:zh": 0, "added:bn": 0, "added:hi": 0,
        "added:ta": 0, "added:te": 0, "added:kn": 0,
        "added:ml": 0, "added:ur": 0,
        "retagged:en": 0, "retagged:pt": 0, "retagged:es": 0,
        "retagged:fr": 0, "retagged:de": 0, "retagged:it": 0,
        "retagged:id": 0, "retagged:zh": 0, "retagged:bn": 0,
        "retagged:hi": 0, "retagged:ta": 0, "retagged:te": 0,
        "retagged:kn": 0, "retagged:ml": 0, "retagged:ur": 0,
    }
    for md in sorted(POSTS_DIR.glob("*.md")):
        result = process_file(md, retag=retag)
        counts[result] = counts.get(result, 0) + 1

    mode_label = "RETAG MODE (force re-detection)" if retag else "normal mode"
    print(f"Language tagging complete ({mode_label}):")
    for k, v in counts.items():
        if v > 0 or k in ("skipped", "unchanged", "no-frontmatter"):
            print(f"  {k:18s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
