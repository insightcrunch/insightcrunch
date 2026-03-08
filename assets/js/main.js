/* InsightCrunch — load-more + search */

const BATCH = 4;

document.addEventListener('DOMContentLoaded', () => {
  initLoadMore();
  initSearch();
});

function initLoadMore() {
  const posts = document.querySelectorAll('#postList .post-card');
  if (!posts.length) return;

  let shown = 0;
  posts.forEach((p, i) => {
    if (i < 5) { p.classList.remove('hidden'); shown++; }
    else        { p.classList.add('hidden'); }
  });

  const wrap = document.getElementById('loadMoreWrap');
  const btn  = document.getElementById('loadMoreBtn');
  const stat = document.getElementById('lmStatus');
  const cnt  = document.getElementById('postCount');

  const total = posts.length;
  if (cnt) cnt.textContent = 'Showing ' + shown + ' of ' + total;
  if (wrap && total > 5) wrap.style.display = 'block';
  updateStatus();

  window.loadMore = function () {
    btn.classList.add('loading');
    btn.textContent = 'Loading\u2026';

    setTimeout(() => {
      let revealed = 0;
      posts.forEach(p => {
        if (p.classList.contains('hidden') && revealed < BATCH) {
          p.classList.remove('hidden');
          p.classList.add('appearing');
          revealed++;
          shown++;
        }
      });

      if (cnt) cnt.textContent = 'Showing ' + shown + ' of ' + total;
      btn.classList.remove('loading');
      btn.textContent = 'Load more posts';
      updateStatus();

      if (shown >= total) {
        btn.classList.add('done');
        btn.textContent = 'All posts loaded';
      }
    }, 500);
  };

  function updateStatus() {
    if (!stat) return;
    const remaining = total - shown;
    stat.textContent = remaining > 0
      ? remaining + ' more post' + (remaining > 1 ? 's' : '') + ' to load'
      : '';
  }
}

function initSearch() {
  const input = document.getElementById('searchInput');
  if (!input) return;

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    const posts = document.querySelectorAll('#postList .post-card');
    const cnt   = document.getElementById('postCount');
    let visible = 0;

    posts.forEach(p => {
      const title = (p.dataset.title || '').toLowerCase();
      const cat   = (p.dataset.cat || '').toLowerCase();
      const tags  = (p.dataset.tags || '').toLowerCase();
      const match = !q || title.includes(q) || cat.includes(q) || tags.includes(q);
      p.style.display = match ? '' : 'none';
      if (match) visible++;
    });

    if (cnt) cnt.textContent = q
      ? visible + ' result' + (visible !== 1 ? 's' : '') + ' for "' + q + '"'
      : 'Showing ' + visible + ' of ' + posts.length;

    const wrap = document.getElementById('loadMoreWrap');
    if (wrap) wrap.style.display = q ? 'none' : '';
  });
}
