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
   Works on every page, two modes:

   Home page (has #postList):
     Phase 1 (instant): hide/show rendered .post-card elements via data-*
     Phase 2 (async):   fetch /search-index.json, append extended results
                        as card-style rows after #postList.
   Other pages (post, category, about — no #postList):
     Only runs Phase 2. Results render into #searchDropdown beneath the
     sidebar search input as card-style rows. Clicking navigates to post.

   Either way, the index is only fetched when search is actually used,
   and the card markup is identical so styling stays consistent.
*/

function isHomeSearchContext() {
  return !!document.getElementById('postList');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, function(c) {
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}

/* Build a single search-result card. Used by both home (appended after
   postList) and post pages (inside #searchDropdown). Identical markup
   ensures identical styling. */
function buildResultCard(item) {
  var title = escapeHtml(item.t || '');
  var url = escapeHtml(item.u || '#');
  var cat = item.c ? escapeHtml(item.c) : '';
  // item.b is the body excerpt, case-preserved. Trim to 140 chars for display
  // and strip trailing "..." that truncate: may have added.
  var excerpt = '';
  if (item.b) {
    var body = item.b.replace(/\.{3,}$/, '').trim();
    if (body.length > 140) body = body.slice(0, 137).replace(/\s+\S*$/, '') + '…';
    excerpt = escapeHtml(body);
  }
  var html =
    '<a class="search-result-card" href="' + url + '">' +
      (cat ? '<div class="src-cat">' + cat + '</div>' : '') +
      '<div class="src-title">' + title + '</div>' +
      (excerpt ? '<div class="src-excerpt">' + excerpt + '</div>' : '') +
    '</a>';
  return html;
}

function filterPosts(q) {
  LAST_QUERY = q;
  var homeCtx = isHomeSearchContext();
  var lmWrap = document.getElementById('lmWrap');
  var dropdown = document.getElementById('searchDropdown');

  if (!q.trim()) {
    // Empty query — restore default state
    var extended = document.getElementById('searchExtended');
    if (extended) extended.remove();
    var emptyState = document.getElementById('searchEmpty');
    if (emptyState) emptyState.remove();
    if (dropdown) { dropdown.hidden = true; dropdown.innerHTML = ''; }

    if (homeCtx) {
      shown = 0;
      allPosts().forEach(function(p, i) {
        p.removeAttribute('data-search-hidden');
        if (i < 5) { p.classList.remove('hidden'); shown++; }
        else        { p.classList.add('hidden'); }
      });
      if (lmWrap) lmWrap.style.display = '';
      updateStatus();
    }
    return;
  }

  var qLower = q.toLowerCase();

  if (homeCtx) {
    // Phase 1: filter rendered cards instantly (no network)
    if (lmWrap) lmWrap.style.display = 'none';
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
  }

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
      if (LAST_QUERY && LAST_QUERY.trim()) {
        renderExtendedResults(LAST_QUERY.toLowerCase(), LAST_QUERY);
      }
    })
    .catch(function() {
      SEARCH_INDEX_LOADING = false;
    });
}

function renderExtendedResults(qLower, qDisplay) {
  if (!SEARCH_INDEX) return;
  var homeCtx = isHomeSearchContext();

  // On home, skip items already rendered as cards so we don't duplicate.
  // On post pages nothing is pre-rendered, so show everything matching.
  var renderedSlugs = {};
  if (homeCtx) {
    allPosts().forEach(function(p) { renderedSlugs[p.dataset.slug] = 1; });
  }

  var extras = [];
  for (var i = 0; i < SEARCH_INDEX.length; i++) {
    var p = SEARCH_INDEX[i];
    if (homeCtx && renderedSlugs[p.s]) continue;
    // Title, category, tags match case-insensitively. Body is case-preserved
    // in the index (doubles as excerpt), so lowercase at search time.
    if ((p.t && p.t.toLowerCase().indexOf(qLower) !== -1) ||
        (p.c && p.c.toLowerCase().indexOf(qLower) !== -1) ||
        (p.g && p.g.toLowerCase().indexOf(qLower) !== -1) ||
        (p.b && p.b.toLowerCase().indexOf(qLower) !== -1)) {
      extras.push(p);
      if (extras.length >= 40) break;
    }
  }

  // Clean up previous render, then render fresh
  var existingEx = document.getElementById('searchExtended');
  if (existingEx) existingEx.remove();
  var existingEmpty = document.getElementById('searchEmpty');
  if (existingEmpty) existingEmpty.remove();

  if (homeCtx) {
    renderHomeExtended(extras, qDisplay);
  } else {
    renderDropdownResults(extras, qDisplay);
  }
}

function renderHomeExtended(extras, qDisplay) {
  var renderedMatchCount = document.querySelectorAll('#postList .post-card:not(.hidden)').length;
  var totalMatches = renderedMatchCount + extras.length;

  if (totalMatches === 0) {
    var empty = document.createElement('div');
    empty.id = 'searchEmpty';
    empty.className = 'search-empty';
    empty.innerHTML = 'No matches for \u201c' + escapeHtml(qDisplay) + '\u201d';
    document.getElementById('postList').insertAdjacentElement('afterend', empty);
    updateCount('0 results for \u201c' + qDisplay + '\u201d');
    return;
  }
  if (extras.length === 0) {
    updateCount(totalMatches + ' result' + (totalMatches !== 1 ? 's' : '') + ' for \u201c' + qDisplay + '\u201d');
    return;
  }

  var frag = document.createElement('div');
  frag.id = 'searchExtended';
  frag.className = 'search-extended';
  var inner = '<div class="src-heading">More matches from the archive</div>';
  inner += '<div class="src-list">';
  for (var j = 0; j < extras.length; j++) {
    inner += buildResultCard(extras[j]);
  }
  inner += '</div>';
  frag.innerHTML = inner;
  document.getElementById('postList').insertAdjacentElement('afterend', frag);
  updateCount(totalMatches + ' result' + (totalMatches !== 1 ? 's' : '') + ' for \u201c' + qDisplay + '\u201d');
}

function renderDropdownResults(extras, qDisplay) {
  var dropdown = document.getElementById('searchDropdown');
  if (!dropdown) return;
  if (extras.length === 0) {
    dropdown.innerHTML = '<div class="src-empty">No matches for \u201c' + escapeHtml(qDisplay) + '\u201d</div>';
    dropdown.hidden = false;
    return;
  }
  var inner = '<div class="src-heading">' + extras.length + ' result' + (extras.length !== 1 ? 's' : '') + ' for \u201c' + escapeHtml(qDisplay) + '\u201d</div>';
  inner += '<div class="src-list">';
  for (var j = 0; j < extras.length; j++) {
    inner += buildResultCard(extras[j]);
  }
  inner += '</div>';
  dropdown.innerHTML = inner;
  dropdown.hidden = false;
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
  if (document.getElementById('postList')) {
    updateStatus();
  }

  // Prefetch search index on first input focus — cheap UX win, still lazy.
  // Runs on every page (home + post + category + about) because the sidebar
  // search input is global.
  var searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('focus', function() {
      if (!SEARCH_INDEX && !SEARCH_INDEX_LOADING) loadSearchIndex();
    }, { once: true });
  }

  // Clicking anywhere outside the sidebar search area closes the dropdown
  // (so users can dismiss results without clearing the input manually).
  var dropdown = document.getElementById('searchDropdown');
  if (dropdown) {
    document.addEventListener('click', function(e) {
      var sbSearch = document.querySelector('.sb-search');
      if (sbSearch && !sbSearch.contains(e.target) && !dropdown.hidden) {
        dropdown.hidden = true;
      }
    });
    // Re-open if user focuses the input again while a query is active
    searchInput.addEventListener('focus', function() {
      if (LAST_QUERY && LAST_QUERY.trim() && dropdown.innerHTML) {
        dropdown.hidden = false;
      }
    });
  }

  // Escape key clears search on any page
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.activeElement === searchInput) {
      searchInput.value = '';
      filterPosts('');
      searchInput.blur();
    }
  });
});
