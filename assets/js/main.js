/* InsightCrunch — load-more + search + sort
   Home page renders first 30 latest posts inline for fast initial paint.
   Beyond 30: Load More button links to /categories/.
   Search: uses rendered cards' data attributes for instant matches,
   then lazy-fetches /search-index.json for full-site body search. */

var shown = 5;
var batch = 4;
var SEARCH_INDEX = null;        // cached JSON index once fetched
var SEARCH_INDEX_LOADING = false;
var LAST_QUERY = '';

function allPosts() {
  return document.querySelectorAll('#postList .post-card');
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
  if (stat) stat.textContent = 'Showing ' + shown + ' of ' + total + ' latest posts';
  if (btn) {
    if (shown >= total) {
      btn.textContent = 'Browse all posts \u2192';
      btn.classList.add('done');
      btn.dataset.browseMode = '1';
    } else {
      btn.textContent = 'Load more posts';
      btn.classList.remove('done');
      btn.dataset.browseMode = '';
    }
  }
  updateCount('Showing ' + shown + ' of ' + total);
}

function loadMore() {
  var btn = document.getElementById('lmBtn');
  // Once all 30 rendered posts are shown, the button navigates to the
  // category index so users can reach posts 31+ without ever re-rendering
  // them into the home page.
  if (btn && btn.dataset.browseMode === '1') {
    window.location.href = '/categories/';
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

/* ─── Search ─────────────────────────────────────────────────────────
   Two-phase strategy:
   Phase 1 (instant): match rendered cards via their data-title/cat/tags
   Phase 2 (async): once /search-index.json arrives, re-run the query
                    against the full-site body index and append any
                    extra matches as lightweight result links.
   This keeps the first keystroke responsive even on slow networks and
   only downloads the index when search is actually used. */

function filterPosts(q) {
  var postList = document.getElementById('postList');
  var lmWrap = document.getElementById('lmWrap');
  LAST_QUERY = q;

  if (!q.trim()) {
    // Restore: show first 5 rendered cards, hide rest, drop extended results
    var extended = document.getElementById('searchExtended');
    if (extended) extended.remove();
    var emptyState = document.getElementById('searchEmpty');
    if (emptyState) emptyState.remove();

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

  // Phase 1: filter rendered cards instantly (no network)
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

  // Phase 2: lazy-load full search index and re-render extended results
  if (!SEARCH_INDEX) {
    if (!SEARCH_INDEX_LOADING) loadSearchIndex();
    return;
  }
  renderExtendedResults(qLower, q);
}

function loadSearchIndex() {
  SEARCH_INDEX_LOADING = true;
  fetch('/search-index.json')
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function(data) {
      SEARCH_INDEX = data;
      SEARCH_INDEX_LOADING = false;
      // Re-run the current query with the freshly loaded index
      if (LAST_QUERY && LAST_QUERY.trim()) {
        renderExtendedResults(LAST_QUERY.toLowerCase(), LAST_QUERY);
      }
    })
    .catch(function() {
      SEARCH_INDEX_LOADING = false;
      // Index unavailable: the Phase 1 rendered-card search is still active,
      // so the user just gets narrower results. Fail quietly.
    });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, function(c) {
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}

function renderExtendedResults(qLower, qDisplay) {
  if (!SEARCH_INDEX) return;

  // Collect slugs already present as rendered cards so we don't duplicate
  var renderedSlugs = {};
  allPosts().forEach(function(p) { renderedSlugs[p.dataset.slug] = 1; });

  var extras = [];
  for (var i = 0; i < SEARCH_INDEX.length; i++) {
    var p = SEARCH_INDEX[i];
    if (renderedSlugs[p.s]) continue; // skip if already in DOM
    if ((p.t && p.t.toLowerCase().indexOf(qLower) !== -1) ||
        (p.c && p.c.toLowerCase().indexOf(qLower) !== -1) ||
        (p.g && p.g.toLowerCase().indexOf(qLower) !== -1) ||
        (p.b && p.b.indexOf(qLower) !== -1)) {
      extras.push(p);
      if (extras.length >= 40) break; // cap to keep rendering cheap
    }
  }

  var existing = document.getElementById('searchExtended');
  if (existing) existing.remove();
  var emptyState = document.getElementById('searchEmpty');
  if (emptyState) emptyState.remove();

  var renderedMatchCount = document.querySelectorAll('#postList .post-card:not(.hidden)').length;
  var totalMatches = renderedMatchCount + extras.length;

  if (totalMatches === 0) {
    var empty = document.createElement('div');
    empty.id = 'searchEmpty';
    empty.className = 'search-empty';
    empty.style.cssText = 'text-align:center;padding:32px 18px;color:var(--soft,#9a8870);font-family:Inter,sans-serif;font-size:13px;';
    empty.innerHTML = 'No matches for \u201c' + escapeHtml(qDisplay) + '\u201d';
    document.getElementById('postList').insertAdjacentElement('afterend', empty);
  }

  if (extras.length === 0) {
    updateCount(totalMatches + ' result' + (totalMatches !== 1 ? 's' : '') + ' for \u201c' + qDisplay + '\u201d');
    return;
  }

  var frag = document.createElement('div');
  frag.id = 'searchExtended';
  frag.className = 'search-extended';
  frag.style.cssText = 'margin-top:16px;';

  var html = '<div style="font-family:Inter,sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--soft,#9a8870);margin-bottom:10px;padding:0 2px;">More matches from the archive</div>';
  html += '<div class="search-extended-list">';
  for (var j = 0; j < extras.length; j++) {
    var item = extras[j];
    html += '<a class="search-result" href="' + escapeHtml(item.u) + '" style="display:block;padding:11px 14px;border-bottom:1px solid var(--rule,#ddd0b8);color:var(--ink,#1a1208);text-decoration:none;transition:background .15s;">';
    html += '<div style="font-family:Lora,serif;font-weight:600;font-size:15px;line-height:1.35;margin-bottom:2px;">' + escapeHtml(item.t || '') + '</div>';
    if (item.c) {
      html += '<div style="font-family:Inter,sans-serif;font-size:11px;color:var(--soft,#9a8870);letter-spacing:.03em;">' + escapeHtml(item.c) + '</div>';
    }
    html += '</a>';
  }
  html += '</div>';
  frag.innerHTML = html;

  document.getElementById('postList').insertAdjacentElement('afterend', frag);
  updateCount(totalMatches + ' result' + (totalMatches !== 1 ? 's' : '') + ' for \u201c' + qDisplay + '\u201d');
}

function setSort(type, el) {
  // visual active state
  document.querySelectorAll('.sort-pill').forEach(function(b) { b.classList.remove('on'); });
  el.classList.add('on');
  // Popular = sort by read_time descending (proxy for engagement)
  // Latest  = original DOM order (already date-sorted by Jekyll)
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

document.addEventListener('DOMContentLoaded', function() {
  updateStatus();

  var hasPostList = document.getElementById('postList');
  if (!hasPostList) return;

  // Prefetch search index on first input focus — cheap UX win, still lazy
  var searchInput = document.querySelector('input[type=search], #searchBox, .search-input');
  if (searchInput) {
    searchInput.addEventListener('focus', function() {
      if (!SEARCH_INDEX && !SEARCH_INDEX_LOADING) loadSearchIndex();
    }, { once: true });
  }
});
