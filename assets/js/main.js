/* InsightCrunch — load-more + search + sort
   Home page renders first 30 latest posts inline for fast initial paint.
   Beyond 30: Load More button links to /categories/.

   Search works on every page, differently by context:
     HOME (has #postList): two-phase local/archive filtering, archive
       matches render as .post-card.src-extra appended INSIDE #postList so
       they inherit all scoped card styling (same border, padding, hover,
       title font, excerpt font). No wrapper, no heading, no category — the
       archive cards blend in as if they were more posts below the top 30.
     POST / CATEGORY / ABOUT (no #postList): typing 3+ chars with a short
       idle pause redirects to /?q=query so the user lands on the home
       page with the same search already executed. */

var shown = 5;
var batch = 4;
var SEARCH_INDEX = null;        // cached JSON index once fetched
var SEARCH_INDEX_LOADING = false;
var LAST_QUERY = '';

/* Random archive feed: once the 30 latest are exhausted, the same button
   injects 4 shuffled older posts per click, reusing the search index and
   the simplified buildExtraCard() view. Shuffled ONCE per visit so batches
   never repeat and never skip. */
var RANDOM_QUEUE = null;        // shuffled pool (index entries minus the 30)
var RANDOM_PTR = 0;             // how far into the shuffled pool we have gone
var RANDOM_PENDING = false;     // a click arrived before the index finished loading

/* Post-page redirect debounce: minimum characters + quiet time before
   navigating to /?q=... so we don't fire a redirect on the first keystroke
   or on a two-letter fragment the user is still typing out. */
var REDIRECT_TIMER = null;
var REDIRECT_DEBOUNCE_MS = 600;
var REDIRECT_MIN_CHARS = 3;

function allPosts() {
  // Exclude archive-result cards (.src-extra). They live inside #postList
  // so they can inherit all the scoped .post-card styles, but they must
  // never be iterated by the Phase-1 dataset filter or the load-more
  // reveal logic.
  return document.querySelectorAll('#postList .post-card:not(.src-extra)');
}

function updateCount(label) {
  var cnt = document.getElementById('postCount');
  if (!cnt) return;
  cnt.textContent = label;
}

function updateStatus() {
  var posts = allPosts();
  var total = posts.length;
  var stat = document.getElementById('lmStatus');
  var btn  = document.getElementById('lmBtn');
  if (btn) {
    if (shown >= total) {
      // All 30 latest are shown. Hand the button over to the random feed.
      btn.textContent = 'More from the archive';
      btn.classList.add('done');
      btn.dataset.browseMode = 'random';
      if (stat) stat.textContent = 'Exploring the full archive';
    } else {
      btn.textContent = 'Load more posts';
      btn.classList.remove('done');
      btn.dataset.browseMode = '';
      if (stat) stat.textContent = 'Showing ' + shown + ' of ' + total + ' latest posts';
    }
  }
  updateCount('Showing ' + shown + ' of ' + total);
}

function loadMore() {
  var btn = document.getElementById('lmBtn');
  if (btn && btn.dataset.browseMode === 'random') {
    loadMoreRandom(btn);
    return;
  }
  btn.textContent = 'Loading\u2026';
  btn.classList.add('loading');

  setTimeout(function() {
    var posts = allPosts();
    var revealed = 0;
    posts.forEach(function(p) {
      if (p.classList.contains('hidden') && !p.dataset.searchHidden && revealed < batch) {
        p.classList.remove('hidden');
        p.classList.add('appearing');
        revealed++;
        shown++;
      }
    });
    btn.classList.remove('loading');
    updateStatus();
  }, 500);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, function(c) {
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}

function isHomePage() {
  return !!document.getElementById('postList');
}

function filterPosts(q) {
  LAST_QUERY = q;

  /* ── POST / CATEGORY / ABOUT pages: redirect-to-home flow ─────────── */
  if (!isHomePage()) {
    clearTimeout(REDIRECT_TIMER);
    var trimmed = q.trim();
    if (trimmed.length >= REDIRECT_MIN_CHARS) {
      REDIRECT_TIMER = setTimeout(function() {
        // Belt-and-braces: only redirect if the input hasn't changed
        // since the timer was set (covers the user hitting backspace
        // inside the idle window).
        var input = document.getElementById('searchInput');
        if (input && input.value.trim() === trimmed) {
          window.location.href = '/?q=' + encodeURIComponent(trimmed);
        }
      }, REDIRECT_DEBOUNCE_MS);
    }
    return;
  }

  /* ── HOME page: filter in-place + append archive extras ───────────── */
  var lmWrap = document.getElementById('lmWrap');

  if (!q.trim()) {
    removeExtraCards();          // also clears any random-injected cards
    var emptyState = document.getElementById('searchEmpty');
    if (emptyState) emptyState.remove();

    // Reset the random feed so it can start fresh after the 30 again.
    RANDOM_PTR = 0;
    var lmBtnReset = document.getElementById('lmBtn');
    if (lmBtnReset) { lmBtnReset.style.display = ''; lmBtnReset.classList.remove('loading'); }

    shown = 0;
    allPosts().forEach(function(p, i) {
      p.removeAttribute('data-search-hidden');
      if (i < 5) { p.classList.remove('hidden'); shown++; }
      else        { p.classList.add('hidden'); }
    });
    if (lmWrap) lmWrap.style.display = '';
    updateStatus();
    return;
  }

  if (lmWrap) lmWrap.style.display = 'none';

  // Phase 1: instant filter of the 30 pre-rendered cards
  var qLower = q.toLowerCase();
  var renderedMatches = 0;
  allPosts().forEach(function(p) {
    var title = (p.dataset.title || '').toLowerCase();
    var cat   = (p.dataset.cat   || '').toLowerCase();
    var tags  = (p.dataset.tags  || '').toLowerCase();
    var match = title.indexOf(qLower) !== -1 ||
                cat.indexOf(qLower)   !== -1 ||
                tags.indexOf(qLower)  !== -1;
    p.classList.toggle('hidden', !match);
    if (match) renderedMatches++;
  });
  updateCount(renderedMatches + ' result' + (renderedMatches !== 1 ? 's' : '') + ' for \u201c' + q + '\u201d');

  // Phase 2: lazy-load full-site index, then re-render archive extras
  if (!SEARCH_INDEX) {
    if (!SEARCH_INDEX_LOADING) loadSearchIndex();
    return;
  }
  renderArchiveExtras(qLower, q);
}

function loadSearchIndex() {
  SEARCH_INDEX_LOADING = true;
  fetch('/search-index.json')
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function(data) {
      SEARCH_INDEX = data;
      SEARCH_INDEX_LOADING = false;
      if (LAST_QUERY && LAST_QUERY.trim() && isHomePage()) {
        renderArchiveExtras(LAST_QUERY.toLowerCase(), LAST_QUERY);
      }
      if (RANDOM_PENDING) {
        RANDOM_PENDING = false;
        loadMoreRandom(document.getElementById('lmBtn'));
      }
    })
    .catch(function() {
      SEARCH_INDEX_LOADING = false;
    });
}

/* Remove only the archive-extra cards — leave the 30 rendered cards and
   their data-state intact. Called on every re-query and on clear. */
function removeExtraCards() {
  var nodes = document.querySelectorAll('#postList .src-extra');
  for (var i = 0; i < nodes.length; i++) nodes[i].remove();
}

/* Build one archive-result card. Uses the SAME classes as the rendered
   post-cards (.post-card, .title, .ex) so the home.html's
   #postList-scoped styles (Newsreader italic 19px title, DM Sans 12.5px
   excerpt, 14px/30px padding, bottom-border-only, amber gradient hover)
   apply with zero additional CSS. The .src-extra class is purely a
   marker for cleanup and exclusion from allPosts() — it has no styles
   of its own. No category tag, no byline, no meta row. */
function buildExtraCard(item) {
  var title = escapeHtml(item.t || '');
  var url   = escapeHtml(item.u || '#');
  var excerpt = '';
  if (item.b) {
    var body = item.b.replace(/\s*\.{3,}\s*$/, '').trim();
    if (body.length > 200) {
      body = body.slice(0, 197).replace(/\s+\S*$/, '') + '\u2026';
    }
    excerpt = escapeHtml(body);
  }
  return '<article class="post-card src-extra" onclick="window.location=\'' + url + '\'">' +
           '<h3 class="title">' + title + '</h3>' +
           (excerpt ? '<p class="ex">' + excerpt + '</p>' : '') +
         '</article>';
}

function renderArchiveExtras(qLower, qDisplay) {
  if (!SEARCH_INDEX) return;

  removeExtraCards();
  var emptyState = document.getElementById('searchEmpty');
  if (emptyState) emptyState.remove();

  // Collect slugs already pre-rendered so we don't duplicate them
  var renderedSlugs = {};
  allPosts().forEach(function(p) { renderedSlugs[p.dataset.slug] = 1; });

  var extras = [];
  for (var i = 0; i < SEARCH_INDEX.length; i++) {
    var p = SEARCH_INDEX[i];
    if (renderedSlugs[p.s]) continue;
    // Title/cat/tags lowercased inline; body (b) is case-preserved in
    // the index so it doubles as display text, so lowercase at search time.
    if ((p.t && p.t.toLowerCase().indexOf(qLower) !== -1) ||
        (p.c && p.c.toLowerCase().indexOf(qLower) !== -1) ||
        (p.g && p.g.toLowerCase().indexOf(qLower) !== -1) ||
        (p.b && p.b.toLowerCase().indexOf(qLower) !== -1)) {
      extras.push(p);
      if (extras.length >= 40) break;
    }
  }

  var postList = document.getElementById('postList');
  var renderedMatchCount = document.querySelectorAll('#postList .post-card:not(.src-extra):not(.hidden)').length;
  var totalMatches = renderedMatchCount + extras.length;

  if (totalMatches === 0) {
    var empty = document.createElement('div');
    empty.id = 'searchEmpty';
    empty.className = 'search-empty';
    empty.style.cssText = 'text-align:center;padding:40px 30px;color:var(--soft,#9a8870);font-family:Inter,sans-serif;font-size:13px;';
    empty.innerHTML = 'No matches for \u201c' + escapeHtml(qDisplay) + '\u201d';
    postList.insertAdjacentElement('afterend', empty);
    updateCount('0 results for \u201c' + qDisplay + '\u201d');
    return;
  }

  if (extras.length) {
    var frag = document.createElement('div');
    frag.innerHTML = extras.map(buildExtraCard).join('');
    while (frag.firstChild) postList.appendChild(frag.firstChild);
  }
  updateCount(totalMatches + ' result' + (totalMatches !== 1 ? 's' : '') + ' for \u201c' + qDisplay + '\u201d');
}

/* ── Random archive feed ─────────────────────────────────────────────
   Reuses SEARCH_INDEX (every post) and buildExtraCard() (the simplified
   title + excerpt card). The pool is shuffled ONCE per visit, so repeat
   clicks walk forward through a fixed order: no repeats, no skips. */

function buildRandomQueue() {
  // Exclude the 30 already-rendered posts so nothing shows twice.
  var renderedSlugs = {};
  allPosts().forEach(function(p) { renderedSlugs[p.dataset.slug] = 1; });

  var pool = [];
  for (var i = 0; i < SEARCH_INDEX.length; i++) {
    if (!renderedSlugs[SEARCH_INDEX[i].s]) pool.push(SEARCH_INDEX[i]);
  }
  // Fisher-Yates shuffle, once.
  for (var j = pool.length - 1; j > 0; j--) {
    var k = Math.floor(Math.random() * (j + 1));
    var tmp = pool[j]; pool[j] = pool[k]; pool[k] = tmp;
  }
  RANDOM_QUEUE = pool;
  RANDOM_PTR = 0;
}

function injectRandomBatch() {
  var postList = document.getElementById('postList');
  if (!postList) return;
  var slice = RANDOM_QUEUE.slice(RANDOM_PTR, RANDOM_PTR + batch);
  RANDOM_PTR += slice.length;
  if (!slice.length) return;

  var before = postList.querySelectorAll('.src-extra').length;
  var frag = document.createElement('div');
  frag.innerHTML = slice.map(buildExtraCard).join('');
  while (frag.firstChild) postList.appendChild(frag.firstChild);

  // Fade the newly appended cards in, matching load-more.
  var all = postList.querySelectorAll('.src-extra');
  for (var i = before; i < all.length; i++) all[i].classList.add('appearing');
}

function finishRandom(btn) {
  var stat = document.getElementById('lmStatus');
  if (stat) stat.textContent = 'You have reached the end of the archive';
  if (btn) btn.style.display = 'none';
}

function loadMoreRandom(btn) {
  if (!btn) return;

  // Index not ready yet: mark the click as pending and fetch it now.
  if (!SEARCH_INDEX) {
    RANDOM_PENDING = true;
    btn.textContent = 'Loading\u2026';
    btn.classList.add('loading');
    if (!SEARCH_INDEX_LOADING) loadSearchIndex();
    return;
  }

  if (!RANDOM_QUEUE) buildRandomQueue();

  if (RANDOM_PTR >= RANDOM_QUEUE.length) { finishRandom(btn); return; }

  btn.textContent = 'Loading\u2026';
  btn.classList.add('loading');
  setTimeout(function() {
    injectRandomBatch();
    btn.classList.remove('loading');
    if (RANDOM_PTR >= RANDOM_QUEUE.length) finishRandom(btn);
    else btn.textContent = 'More from the archive';
  }, 400);
}

function setSort(type, el) {
  document.querySelectorAll('.sort-pill').forEach(function(b) { b.classList.remove('on'); });
  el.classList.add('on');
  var list  = document.getElementById('postList');
  var cards = Array.from(allPosts());
  if (type === 'popular') {
    cards.sort(function(a, b) {
      var ra = parseInt((a.querySelector('.post-mins')||{}).textContent) || 0;
      var rb = parseInt((b.querySelector('.post-mins')||{}).textContent) || 0;
      return rb - ra;
    });
  } else {
    cards.sort(function(a, b) { return parseInt(a.dataset.index) - parseInt(b.dataset.index); });
  }
  cards.forEach(function(c, i) {
    list.appendChild(c);
    c.classList.toggle('hidden', i >= shown);
    c.classList.toggle('featured', i === 0);
  });
  updateStatus();
}

/* Auto-apply ?q=... URL param on home page load. This is how searches
   initiated on post pages (via the redirect flow) land and execute. */
function applyInitialQuery() {
  if (!isHomePage()) return;
  var params = new URLSearchParams(window.location.search);
  var q = params.get('q');
  if (!q) return;
  var input = document.getElementById('searchInput');
  if (!input) return;
  input.value = q;
  // Kick off index load now so archive extras appear as soon as possible
  if (!SEARCH_INDEX && !SEARCH_INDEX_LOADING) loadSearchIndex();
  filterPosts(q);
}

document.addEventListener('DOMContentLoaded', function() {
  if (isHomePage()) {
    updateStatus();
    applyInitialQuery();
  }

  // Prefetch the index on first input focus — cheap UX win on any page
  var searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('focus', function() {
      if (!SEARCH_INDEX && !SEARCH_INDEX_LOADING) loadSearchIndex();
    }, { once: true });
  }
});
