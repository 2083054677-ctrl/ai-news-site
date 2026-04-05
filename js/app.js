/* ═══════════════════════════════════════════════════════════
   AI Insight Daily — App Logic
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  let articles = [];
  let activeTag = 'all';
  let searchQuery = '';

  const TAG_COLORS = {
    'AI': 'blue', '大模型': 'purple', 'LLM': 'purple', 'GPT': 'purple', 'Claude': 'purple',
    '研究': 'blue', '论文': 'blue', '学术': 'blue', 'Research': 'blue',
    '产品': 'orange', '发布': 'orange', '更新': 'orange', 'Product': 'orange',
    '开源': 'green', 'GitHub': 'green', 'Open Source': 'green',
    '行业': 'red', '商业': 'red', '融资': 'red', 'Industry': 'red',
  };

  function getTagColor(tag) { return TAG_COLORS[tag] || 'gray'; }

  async function loadArticles() {
    try {
      const res = await fetch('data/articles.json?t=' + Date.now());
      articles = await res.json();
      articles.sort((a, b) => new Date(b.date) - new Date(a.date));
      renderAll();
    } catch (e) {
      console.error('Load failed:', e);
      document.getElementById('cardGrid').innerHTML =
        '<p style="text-align:center;color:var(--text-3);padding:60px;">数据加载失败</p>';
    }
  }

  function renderAll() { renderStats(); renderTags(); renderCards(); }

  function renderStats() {
    document.getElementById('statTotal').textContent = articles.length;
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 864e5);
    document.getElementById('statWeek').textContent = articles.filter(a => new Date(a.date) >= weekAgo).length;
    const allTags = new Set();
    articles.forEach(a => (a.tags || []).forEach(t => allTags.add(t)));
    document.getElementById('statTags').textContent = allTags.size;
    if (articles.length > 0) {
      document.getElementById('statLatest').textContent = fmtDate(articles[0].date);
    }
  }

  function renderTags() {
    const allTags = new Set();
    articles.forEach(a => (a.tags || []).forEach(t => allTags.add(t)));
    const bar = document.getElementById('filterBar');
    bar.innerHTML = '<button class="tag-btn active" data-tag="all">全部</button>';
    allTags.forEach(tag => {
      const b = document.createElement('button');
      b.className = 'tag-btn';
      b.dataset.tag = tag;
      b.textContent = tag;
      bar.appendChild(b);
    });
    bar.querySelectorAll('.tag-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        activeTag = btn.dataset.tag;
        bar.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderCards();
      });
    });
  }

  function getFiltered() {
    return articles.filter(a => {
      const mt = activeTag === 'all' || (a.tags || []).includes(activeTag);
      const ms = !searchQuery ||
        a.title.toLowerCase().includes(searchQuery) ||
        a.summary.toLowerCase().includes(searchQuery) ||
        (a.author || '').toLowerCase().includes(searchQuery) ||
        (a.tags || []).some(t => t.toLowerCase().includes(searchQuery));
      return mt && ms;
    });
  }

  function renderCards() {
    const list = getFiltered();
    const grid = document.getElementById('cardGrid');
    const empty = document.getElementById('emptyState');
    if (!list.length) { grid.innerHTML = ''; empty.style.display = 'block'; return; }
    empty.style.display = 'none';
    grid.innerHTML = list.map(a => `
      <article class="article-card" data-id="${a.id}">
        <div class="card-tags">
          ${(a.tags || []).map(t => `<span class="card-tag" data-color="${getTagColor(t)}">${esc(t)}</span>`).join('')}
        </div>
        <h3 class="card-title">${esc(a.title)}</h3>
        <p class="card-summary">${esc(a.summary)}</p>
        <div class="card-footer">
          <span class="card-author">${esc(a.author || '匿名')}</span>
          <span class="card-date">${fmtDate(a.date)}</span>
        </div>
      </article>
    `).join('');
    grid.querySelectorAll('.article-card').forEach(c => {
      c.addEventListener('click', () => {
        const a = articles.find(x => x.id === c.dataset.id);
        if (a) openModal(a);
      });
    });
  }

  function openModal(a) {
    document.getElementById('modalTitle').textContent = a.title;
    document.getElementById('modalMeta').innerHTML =
      `<span>${esc(a.author || '匿名')}</span><span>${fmtDate(a.date)}</span>` +
      (a.source ? `<a href="${esc(a.source)}" target="_blank" rel="noopener">查看来源</a>` : '');
    document.getElementById('modalTags').innerHTML =
      (a.tags || []).map(t => `<span class="card-tag" data-color="${getTagColor(t)}">${esc(t)}</span>`).join('');
    const txt = (a.content || a.summary || '');
    document.getElementById('modalBody').innerHTML = txt.split(/\n+/)
      .filter(p => p.trim())
      .map(p => `<p>${esc(p.trim())}</p>`)
      .join('');
    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
  }

  function initTheme() {
    const s = localStorage.getItem('theme');
    document.documentElement.dataset.theme = s || 'dark';
  }

  function toggleTheme() {
    const n = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = n;
    localStorage.setItem('theme', n);
  }

  function fmtDate(d) {
    if (!d) return '—';
    const o = new Date(d);
    return `${o.getFullYear()}-${String(o.getMonth()+1).padStart(2,'0')}-${String(o.getDate()).padStart(2,'0')}`;
  }

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function bind() {
    document.getElementById('searchInput').addEventListener('input', e => {
      searchQuery = e.target.value.trim().toLowerCase();
      renderCards();
    });
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', e => {
      if (e.target === e.currentTarget) closeModal();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  }

  function init() { initTheme(); bind(); loadArticles(); }
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
})();
