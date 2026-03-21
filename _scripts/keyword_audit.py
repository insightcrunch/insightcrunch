#!/usr/bin/env python3
"""
Keyword Audit - Detects posts where proper nouns (cities, companies,
technologies) appear in the URL slug or title but are absent from the
page_title and/or body.  Outputs admin/keyword-audit-data.json consumed
by the admin Keyword Audit page.

Run:  python _scripts/keyword_audit.py
"""

import json, os, re, sys
from datetime import datetime, timezone

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')
OUT_FILE  = os.path.join(os.path.dirname(__file__), '..', 'admin', 'keyword-audit-data.json')

# ── Known proper-noun dictionary (expandable) ───────────────────────
KNOWN_CITIES = {
    'ahmedabad','ahmadabad','bangalore','bengaluru','bhopal','bhubaneswar',
    'chandigarh','chennai','coimbatore','delhi','gandhinagar','goa',
    'gurgaon','gurugram','guwahati','haldia','hyderabad','indore',
    'jaipur','kochi','kolkata','lucknow','mumbai','nagpur','noida',
    'patna','pune','thiruvananthapuram','trivandrum','vadodara','baroda',
    'vizag','visakhapatnam','tokyo','london','paris','berlin','sydney',
    'beijing','shanghai','singapore','dubai','toronto','chicago',
    'francisco','angeles','york','seattle','boston','denver','austin',
    'portland','atlanta','houston','dallas','detroit','minneapolis',
    'orlando','miami','tampa','phoenix','sacramento','pittsburgh',
    'philadelphia','washington','baltimore','richmond','raleigh',
    'charlotte','nashville','memphis','milwaukee','columbus','cincinnati',
    'cleveland','indianapolis','louisville','jacksonville','tucson',
    'sacramento','oakland','diego','jose',
}

KNOWN_COMPANIES = {
    'tcs','infosys','wipro','cognizant','accenture','hcl','capgemini',
    'deloitte','kpmg','ey','pwc','ibm','google','microsoft','amazon',
    'apple','meta','facebook','netflix','twitter','tesla','uber','airbnb',
    'spotify','slack','zoom','oracle','sap','salesforce','adobe','intel',
    'nvidia','amd','qualcomm','samsung','sony','lg','huawei','xiaomi',
    'lenovo','dell','hp','asus','satyam','mahindra',
}

KNOWN_TECH = {
    'python','java','javascript','typescript','react','angular','vue',
    'django','flask','nodejs','ruby','rails','php','laravel','swift',
    'kotlin','rust','golang','scala','hadoop','spark','kafka','redis',
    'mongodb','postgresql','mysql','elasticsearch','docker','kubernetes',
    'terraform','ansible','jenkins','tableau','powerbi','excel','chromebook',
    'android','ios','linux','ubuntu','windows','macos',
}

KNOWN_EXAMS = {
    'upsc','cat','gre','gmat','gate','nqt','ielts','toefl','gaokao',
    'iit','nit','iisc','jee','neet','ssc','ibps',
}

KNOWN_PROGRAMS = {
    'ilp','itis','itp','aspire','codevita','ccqt',
}

ALL_PROPER = KNOWN_CITIES | KNOWN_COMPANIES | KNOWN_TECH | KNOWN_EXAMS | KNOWN_PROGRAMS

# Stopwords that never count as proper nouns even if capitalised in title
STOPWORDS = {
    'a','an','the','of','in','to','for','and','or','is','are','was','were',
    'how','what','why','when','where','which','who','that','this','with',
    'your','you','my','our','its','can','will','do','does','did','be',
    'been','being','have','has','had','not','but','from','on','at','by',
    'as','if','so','no','all','about','up','out','just','into','over',
    'after','before','between','through','during','without','within',
    'should','could','would','may','might','must','shall','need','get',
    'got','make','made','take','best','top','most','every','each','more',
    'new','way','ways','things','thing','really','know','like','vs','step',
    'guide','tips','tricks','complete','ultimate','simple','easy',
    'important','key','essential','effective','common','great','good',
    'better','still','any','some','many','few','other','much','very',
    'also','too','than','then','here','there','now','only','even',
    'first','last','next','also','experience','journey','day',
    'questions','answers','preparation','practice','mock','test',
    'strategy','detailed','analysis','comparison','review','process',
    'hiring','interview','salary','package','date','batch','joining',
    'accommodation','hostel','housing','campus','training','centre',
    'center','life','daily','rules','survival','cracking','fail',
    'project','allocation','results','score','predict','community',
    'students','freshers','employees','candidates','beginners',
    'complete','everything','explained','breakdown','comprehensive',
    'documents','required','checklist','streams','domains','ratings',
    'deductions','centers','dos','donts',
}


def parse_front_matter(text):
    """Extract YAML front matter fields we care about."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return None, ''
    fm_text = m.group(1)
    body = text[m.end():]

    def get_field(name):
        pat = re.compile(rf'^{name}:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
        hit = pat.search(fm_text)
        return hit.group(1).strip() if hit else ''

    return {
        'title':      get_field('title'),
        'page_title': get_field('page_title'),
        'date':       get_field('date'),
        'categories': get_field('categories'),
    }, body


def slug_tokens(filename):
    """Return lowercase word tokens from the slug portion of the filename."""
    slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', filename).replace('.md', '')
    return [t for t in slug.split('-') if len(t) > 1]


def title_proper_nouns(title):
    """Identify words in the title that are capitalised (proper nouns)
       or match the known dictionary."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9']*", title)
    result = set()
    for w in words:
        low = w.lower()
        if low in STOPWORDS:
            continue
        # Capitalised in title (first word excluded unless also in known set)
        if w[0].isupper() or low in ALL_PROPER:
            result.add(low)
    return result


def detect_issues(filename, fm, body):
    """Return list of issue dicts for a single post."""
    issues = []
    slug_words = set(slug_tokens(filename))
    page_title = fm.get('page_title', '').lower()
    body_lower = body.lower()
    title_lower = fm['title'].lower()

    # Only flag words that are in the known proper-noun dictionary.
    # This avoids false positives on common English words like "chaos",
    # "secrets", "toolbar" etc. that happen to be capitalised in titles.
    candidates = set()
    for w in slug_words:
        if w in ALL_PROPER:
            candidates.add(w)
    # Also check title words against the dictionary
    title_tokens = set(re.findall(r'[a-zA-Z]+', fm['title'].lower()))
    for w in title_tokens:
        if w in ALL_PROPER and w not in STOPWORDS:
            candidates.add(w)

    if not candidates:
        return issues

    for word in sorted(candidates):
        in_title = word in title_lower
        in_slug  = word in slug_words
        in_page_title = word in page_title if page_title else None
        body_count = len(re.findall(r'\b' + re.escape(word) + r'\b', body_lower))
        word_count = len(body.split())

        severity = 'ok'
        detail = ''

        # ── Check page_title ──
        if page_title and in_title and not in_page_title:
            issues.append({
                'keyword': word,
                'type': 'MISSING_FROM_PAGE_TITLE',
                'severity': 'critical',
                'detail': f'"{word}" is in the title but absent from page_title',
                'in_slug': in_slug,
                'in_title': in_title,
                'in_page_title': False,
                'body_mentions': body_count,
            })

        if not page_title and in_title:
            issues.append({
                'keyword': word,
                'type': 'NO_PAGE_TITLE',
                'severity': 'warning',
                'detail': f'Post has no page_title field at all; "{word}" only in title',
                'in_slug': in_slug,
                'in_title': in_title,
                'in_page_title': None,
                'body_mentions': body_count,
            })

        # ── Check body ──
        if in_slug and body_count == 0:
            issues.append({
                'keyword': word,
                'type': 'SLUG_KEYWORD_MISSING_FROM_BODY',
                'severity': 'critical',
                'detail': f'"{word}" is in the URL slug but never appears in the body',
                'in_slug': True,
                'in_title': in_title,
                'in_page_title': in_page_title,
                'body_mentions': 0,
            })
        elif in_slug and word_count > 2000 and body_count < 3:
            issues.append({
                'keyword': word,
                'type': 'SLUG_KEYWORD_SPARSE_IN_BODY',
                'severity': 'warning',
                'detail': f'"{word}" is in the URL slug but only {body_count}x in {word_count} words',
                'in_slug': True,
                'in_title': in_title,
                'in_page_title': in_page_title,
                'body_mentions': body_count,
            })

        if in_title and not in_slug and body_count == 0:
            issues.append({
                'keyword': word,
                'type': 'TITLE_KEYWORD_MISSING_FROM_BODY',
                'severity': 'critical',
                'detail': f'"{word}" is in the title but never appears in the body',
                'in_slug': False,
                'in_title': True,
                'in_page_title': in_page_title,
                'body_mentions': 0,
            })
        elif in_title and not in_slug and word_count > 2000 and body_count < 3:
            issues.append({
                'keyword': word,
                'type': 'TITLE_KEYWORD_SPARSE_IN_BODY',
                'severity': 'warning',
                'detail': f'"{word}" is in the title but only {body_count}x in {word_count} words',
                'in_slug': False,
                'in_title': True,
                'in_page_title': in_page_title,
                'body_mentions': body_count,
            })

    return issues


def main():
    posts_dir = os.path.normpath(POSTS_DIR)
    out_file  = os.path.normpath(OUT_FILE)

    if not os.path.isdir(posts_dir):
        print(f"ERROR: {posts_dir} not found", file=sys.stderr)
        sys.exit(1)

    results = []
    total_posts = 0
    total_clean = 0

    for fname in sorted(os.listdir(posts_dir)):
        if not fname.endswith('.md'):
            continue
        total_posts += 1

        with open(os.path.join(posts_dir, fname), 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        fm, body = parse_front_matter(content)
        if fm is None:
            continue

        issues = detect_issues(fname, fm, body)

        if issues:
            # Deduplicate: same keyword can only trigger one issue per type
            seen = set()
            deduped = []
            for iss in issues:
                key = (iss['keyword'], iss['type'])
                if key not in seen:
                    seen.add(key)
                    deduped.append(iss)

            slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', fname).replace('.md', '')
            results.append({
                'filename': fname,
                'slug': slug,
                'url': '/' + fname.replace('.md', '/').replace(
                    re.match(r'(\d{4})-(\d{2})-(\d{2})-', fname).group(0),
                    f"{fname[:4]}/{fname[5:7]}/{fname[8:10]}/"),
                'title': fm['title'],
                'page_title': fm['page_title'],
                'has_page_title': bool(fm['page_title']),
                'date': fm['date'],
                'word_count': len(body.split()),
                'issues': deduped,
                'critical_count': sum(1 for i in deduped if i['severity'] == 'critical'),
                'warning_count': sum(1 for i in deduped if i['severity'] == 'warning'),
            })
        else:
            total_clean += 1

    # Sort: critical-heavy first, then by date descending
    results.sort(key=lambda r: (-r['critical_count'], -r['warning_count'], r['date']), reverse=False)
    results.sort(key=lambda r: (-r['critical_count'], -r['warning_count']))

    output = {
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_posts': total_posts,
        'flagged_posts': len(results),
        'clean_posts': total_clean,
        'posts': results,
    }

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Keyword audit complete: {total_posts} posts scanned, "
          f"{len(results)} flagged, {total_clean} clean.")
    print(f"Output: {out_file}")


if __name__ == '__main__':
    main()
