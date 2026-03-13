/* InsightCrunch — load-more + search + sort */

var shown = 5;
var batch = 4;

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
  if (stat) stat.textContent = 'Showing ' + shown + ' of ' + total + ' posts';
  if (btn) {
    if (shown >= total) {
      btn.textContent = 'All posts loaded';
      btn.classList.add('done');
    } else {
      btn.textContent = 'Load more posts';
      btn.classList.remove('done');
    }
  }
  updateCount('Showing ' + shown + ' of ' + total);
}

function loadMore() {
  var btn = document.getElementById('lmBtn');
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

function filterPosts(q) {
  var posts = allPosts();
  var lmWrap = document.getElementById('lmWrap');
  var total = posts.length;

  if (!q.trim()) {
    // restore: show first 5, hide rest
    shown = 0;
    posts.forEach(function(p, i) {
      p.removeAttribute('data-search-hidden');
      if (i < 5) { p.classList.remove('hidden'); shown++; }
      else        { p.classList.add('hidden'); }
    });
    if (lmWrap) lmWrap.style.display = '';
    updateStatus();
    return;
  }

  // searching: show all matches, hide load-more
  if (lmWrap) lmWrap.style.display = 'none';
  var count = 0;
  posts.forEach(function(p) {
    var title = (p.dataset.title || '').toLowerCase();
    var cat   = (p.dataset.cat   || '').toLowerCase();
    var tags  = (p.dataset.tags  || '').toLowerCase();
    var body  = (p.dataset.body  || '').toLowerCase();
    var match = title.includes(q.toLowerCase()) || cat.includes(q.toLowerCase()) || tags.includes(q.toLowerCase()) || body.includes(q.toLowerCase());
    p.classList.toggle('hidden', !match);
    if (match) count++;
  });
  updateCount(count + ' result' + (count !== 1 ? 's' : '') + ' for \u201c' + q + '\u201d');
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

  var input = document.getElementById('searchInput');
  var hasPostList = document.getElementById('postList');

  if (input && hasPostList) {
    // Home / category page: filter in-page
    input.addEventListener('input', function() { filterPosts(this.value); });

    // Auto-search if arrived with ?q= param
    var params = new URLSearchParams(window.location.search);
    var qParam = params.get('q');
    if (qParam) {
      input.value = qParam;
      filterPosts(qParam);
    }
  } else if (input) {
    // Post / other page: redirect to home with query
    var redirectTimer;
    input.addEventListener('input', function() {
      var val = this.value.trim();
      clearTimeout(redirectTimer);
      if (val.length > 2) {
        redirectTimer = setTimeout(function() {
          window.location.href = '/?q=' + encodeURIComponent(val);
        }, 1000);
      }
    });
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        var val = this.value.trim();
        if (val) {
          clearTimeout(redirectTimer);
          window.location.href = '/?q=' + encodeURIComponent(val);
        }
      }
    });
  }

  // ── Copy intercept: first sentence + "Continue reading at URL" ──
  document.addEventListener('copy', function(e) {
    var sel = window.getSelection();
    if (!sel || !sel.toString().trim()) return;

    var raw = sel.toString().trim();

    // Extract first sentence: split on . ! or ? followed by a space or end
    var match = raw.match(/^[\s\S]*?[.!?](?=\s|$)/);
    var firstSentence = match ? match[0].trim() : raw;

    var url = window.location.href;
    var output = firstSentence + '\n\nContinue reading at ' + url;

    e.preventDefault();
    e.clipboardData.setData('text/plain', output);
  });
});
