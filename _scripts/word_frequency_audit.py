#!/usr/bin/env python3
"""
Word Frequency Audit - Detects posts where non-stop-words appear
excessively, indicating filler-word padding rather than substantive content.
Outputs admin/word-frequency-data.json consumed by the admin Word Frequency page.

Run:  python _scripts/word_frequency_audit.py
"""

import json, os, re, sys
from collections import Counter
from datetime import datetime, timezone

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts')
OUT_FILE  = os.path.join(os.path.dirname(__file__), '..', 'admin', 'word-frequency-data.json')

DEFAULT_THRESHOLD = 50

# ── Stop words by language ───────────────────────────────────────
STOP_EN = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'by','from','as','is','are','was','were','be','been','being','have',
    'has','had','do','does','did','will','would','could','should','may',
    'might','shall','can','must','need','not','no','nor','so','if','then',
    'than','that','this','these','those','it','its','he','she','they',
    'we','you','i','me','my','his','her','our','your','their','them',
    'us','him','who','which','what','when','where','how','why','all',
    'each','every','both','few','more','most','other','some','such','any',
    'only','own','same','also','just','very','even','still','already',
    'about','after','again','before','between','during','into','through',
    'above','below','up','down','out','off','over','under','here','there',
    'because','since','while','although','though','until','unless','once',
    'too','much','many','well','back','now','new','like','make','made',
    'get','got','go','went','gone','come','came','take','took','taken',
    'know','knew','known','see','saw','seen','think','thought','say','said',
    'tell','told','give','gave','given','find','found','work','become',
    'became','leave','left','call','called','keep','kept','let','begin',
    'began','seem','seemed','help','show','showed','shown','turn','turned',
    'set','put','run','move','live','believe','bring','brought','happen',
    'write','wrote','written','provide','sit','stand','lose','lost','pay',
    'meet','met','include','continue','long','part','first','last','next',
    'great','good','better','best','right','used','old','year','years',
    'way','ways','day','days','time','world','life','people','man','men',
    'woman','women','thing','things','hand','upon','two','three','one',
    'often','never','always','sometimes','however','therefore','thus',
    'yet','per','among','within','without','across','against','along',
    'around','behind','beyond','towards','whether','de','la','el','en',
    'able','another','away','case','different','early','end','enough',
    'far','form','given','high','home','house','important','kind','large',
    'later','less','line','look','looked','name','number','order','own',
    'place','point','possible','rather','real','seem','several','side',
    'since','small','something','state','still','system','use','water',
    'well','where','while','whole','word','young','may','might','much',
    'must','need','new','number','off','often','old','one','only','open',
    'other','over','own','part','people','place','point','possible',
}

STOP_BN = {
    'এবং','ও','তার','এই','যে','এক','করে','হয়','থেকে','না','সে','তা',
    'আর','কিন্তু','বা','যা','এর','তারা','আমি','আমার','তুমি','তোমার',
    'নিয়ে','হয়ে','করা','করেন','করতে','করি','আছে','আছেন','ছিল','ছিলেন',
    'হবে','দিয়ে','পর','কারণ','জন্য','মধ্যে','সব','কিছু','যখন','তখন',
    'আবার','অনেক','খুব','শুধু','কোনো','প্রতি','নতুন','বড়','ভালো',
}

STOP_HI = {
    'और','के','का','की','है','में','को','से','पर','ने','यह','वह','भी',
    'नहीं','एक','हो','कि','था','या','तो','हैं','जो','इस','कर','लिए',
    'अपने','होता','बहुत','साथ','लेकिन','जैसे','कुछ','उन','ये','रहा',
    'अब','जब','तक','सबसे','फिर','सकता','अगर','ही','ऐसे','उसे',
}

STOP_ZH = {
    '的','了','在','是','我','有','和','就','不','人','都','一','一个',
    '上','也','很','到','说','要','去','你','会','着','没有','看','好',
    '自己','这','那','她','他','它','们','年','大','来','以','个','中',
    '为','与','而','等','被','从','对','或','但','如','可以','这个',
    '因为','所以','如果','虽然','不过','已经','可能','应该','非常',
    '通过','之间','之后','之前','关于','这些','那些','一些','没有',
    '什么','怎么','哪里','谁','如何','为什么','多少','更','最',
}

STOP_WORDS = {
    'en': STOP_EN,
    'bn': STOP_BN,
    'hi': STOP_HI,
    'zh': STOP_ZH,
}


def parse_front_matter(text):
    """Extract YAML front matter fields."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return None, ''
    fm_text = m.group(1)
    body = text[m.end():]

    def get_field(name):
        pat = re.compile(rf'^{name}:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
        hit = pat.search(fm_text)
        return hit.group(1).strip() if hit else ''

    def get_list(name):
        raw = get_field(name)
        if raw.startswith('['):
            return [x.strip().strip('"').strip("'") for x in raw.strip('[]').split(',') if x.strip()]
        return [raw] if raw else []

    return {
        'title':      get_field('title'),
        'categories': get_list('categories'),
        'lang':       get_field('lang') or 'en',
        'wf_ok':      get_field('word_frequency_ok').lower() == 'true',
        'wf_reason':  get_field('word_frequency_ok_reason'),
    }, body


def strip_markup(text):
    """Remove HTML tags, markdown formatting, YAML front matter leftovers."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    text = re.sub(r'[#*_`~|>]+', ' ', text)
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'\{[%{].*?[%}]\}', ' ', text)
    return text


def tokenize_and_count(text, lang):
    """Tokenize text and count word frequencies, excluding stop words."""
    stops = STOP_WORDS.get(lang, STOP_EN)

    if lang == 'zh':
        # For Chinese: count bigrams and individual characters > 1 char
        chars = re.findall(r'[\u4e00-\u9fff]+', text)
        tokens = []
        for run in chars:
            for i in range(len(run) - 1):
                bigram = run[i:i+2]
                if bigram not in stops:
                    tokens.append(bigram)
    else:
        words = re.findall(r"[a-zA-Z\u0980-\u09FF\u0900-\u097F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F\u0600-\u06FF]{2,}", text.lower())
        tokens = [w for w in words if w not in stops]

    return Counter(tokens)


def filename_to_edit_url(filename):
    """Build GitHub edit URL from filename."""
    return 'https://github.com/insightcrunch/insightcrunch/edit/main/_posts/' + filename


def slug_from_filename(filename):
    """Extract slug from post filename."""
    return re.sub(r'^\d{4}-\d{2}-\d{2}-', '', filename).replace('.md', '')


def main():
    if not os.path.isdir(POSTS_DIR):
        print(f'Posts directory not found: {POSTS_DIR}', file=sys.stderr)
        sys.exit(1)

    files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')])
    print(f'Scanning {len(files)} posts for word frequency...')

    results = []
    flagged_count = 0
    worst_word = ''
    worst_count = 0
    worst_post = ''
    total_top_counts = []

    for filename in files:
        filepath = os.path.join(POSTS_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        fm, body = parse_front_matter(content)
        if fm is None:
            continue

        clean = strip_markup(body)
        lang = fm.get('lang', 'en')
        counter = tokenize_and_count(clean, lang)

        if not counter:
            continue

        top20 = counter.most_common(20)
        word_count = sum(counter.values())
        top_word, top_count = top20[0] if top20 else ('', 0)

        total_top_counts.append(top_count)

        # Determine flagged words (above threshold)
        flagged_words = [(w, c) for w, c in top20 if c > DEFAULT_THRESHOLD]
        wf_ok = fm.get('wf_ok', False)
        is_flagged = len(flagged_words) > 0 and not wf_ok

        if is_flagged:
            flagged_count += 1

        # Track worst offender
        if top_count > worst_count:
            worst_count = top_count
            worst_word = top_word
            worst_post = fm.get('title', filename)

        slug = slug_from_filename(filename)

        entry = {
            'filename': filename,
            'slug': slug,
            'title': fm.get('title', ''),
            'categories': fm.get('categories', []),
            'lang': lang,
            'wordCount': word_count,
            'topWord': top_word,
            'topCount': top_count,
            'flagged': is_flagged,
            'suppressed': wf_ok and len(flagged_words) > 0,
            'suppressReason': fm.get('wf_reason', '') if wf_ok else '',
            'editUrl': filename_to_edit_url(filename),
        }

        # Include full detail for flagged OR suppressed posts (lean JSON)
        if is_flagged or entry.get('suppressed'):
            entry['flaggedWords'] = [{'word': w, 'count': c} for w, c in flagged_words]
            entry['top20'] = [{'word': w, 'count': c} for w, c in top20]

        results.append(entry)

    avg_top = round(sum(total_top_counts) / len(total_top_counts), 1) if total_top_counts else 0
    suppressed_count = sum(1 for r in results if r.get('suppressed'))

    output = {
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'threshold': DEFAULT_THRESHOLD,
        'totalPosts': len(results),
        'flaggedPosts': flagged_count,
        'suppressedPosts': suppressed_count,
        'worstWord': worst_word,
        'worstCount': worst_count,
        'worstPost': worst_post,
        'avgTopCount': avg_top,
        'posts': results,
    }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'Done. {len(results)} posts scanned, {flagged_count} flagged.')
    print(f'Worst: "{worst_word}" ({worst_count}x) in "{worst_post}"')
    print(f'Output: {OUT_FILE}')


if __name__ == '__main__':
    main()
