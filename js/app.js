/* ═══════════════════════════════════════════════════════════
   AI Insight Daily — App Logic
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── State ──
  let articles = [];
  let activeTag = 'all';
  let searchQuery = '';

  // ── Tag color mapping ──
  const TAG_COLORS = {
    'AI': 'blue', '大模型': 'blue', 'LLM': 'blue', 'GPT': 'blue', 'Claude': 'blue',
    '研究': 'purple', '论文': 'purple', '学术': 'purple', 'Research': 'purple',
    '产品': 'orange', '发布': 'orange', '更新': 'orange', 'Product': 'orange',
    '开源': 'green', 'GitHub': 'green', 'Open Source': 'green',
    '行业': 'red', '商业': 'red', '融资': 'red', 'Industry': 'red',
  };

  function getTagColor(tag) {
    return TAG_COLORS[tag] || 'gray';
  }

  // ── Load Data ──
  async function loadArticles() {
    try {
      const res = await fetch('data/articles.json?t=' + Date.now());
      articles = await res.json();
      articles.sort((a, b) => new Date(b.date) - new Date(a.date));
      renderAll();
    } catch (e) {
      console.error('Failed to load articles:', e);
      document.getElementById('cardGrid').innerHTML =
        '<p style="text-align:center;color:var(--text-tertiary);padding:40px;">加载失败，请检查 data/articles.json</p>';
    }
  }

  // ── Render Everything ──
  function renderAll() {
    renderStats();
    renderTags();
    renderCards();
  }

  // ── Stats ──
  function renderStats() {
    document.getElementById('statTotal').textContent = articles.length;

    // This week count
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const weekCount = articles.filter(a => new Date(a.date) >= weekAgo).length;
    document.getElementById('statWeek').textContent = weekCount;

    // Unique tags
    const allTags = new Set();
    articles.forEach(a => (a.tags || []).forEach(t => allTags.add(t)));
    document.getElementById('statTags').textContent = allTags.size;

    // Latest date
    if (articles.length > 0) {
      const latest = articles[0].date;
      document.getElementById('statLatest').textContent = formatDate(latest);
    }
  }

  // ── Tags ──
  function renderTags() {
    const allTags = new Set();
    articles.forEach(a => (a.tags || []).forEach(t => allTags.add(t)));

    const bar = document.getElementById('filterBar');
    bar.innerHTML = '<button class="tag-btn active" data-tag="all">全部</button>';
    allTags.forEach(tag => {
      const btn = document.createElement('button');
      btn.className = 'tag-btn';
      btn.dataset.tag = tag;
      btn.textContent = tag;
      bar.appendChild(btn);
    });

    // Bind clicks
    bar.querySelectorAll('.tag-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        activeTag = btn.dataset.tag;
        bar.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderCards();
      });
    });
  }

  // ── Filter ──
  function getFilteredArticles() {
    return articles.filter(a => {
      const matchTag = activeTag === 'all' || (a.tags || []).includes(activeTag);
      const matchSearch = !searchQuery ||
        a.title.toLowerCase().includes(searchQuery) ||
        a.summary.toLowerCase().includes(searchQuery) ||
        (a.author || '').toLowerCase().includes(searchQuery) ||
        (a.tags || []).some(t => t.toLowerCase().includes(searchQuery));
      return matchTag && matchSearch;
    });
  }

  // ── Render Cards ──
  function renderCards() {
    const filtered = getFilteredArticles();
    const grid = document.getElementById('cardGrid');
    const empty = document.getElementById('emptyState');

    if (filtered.length === 0) {
      grid.innerHTML = '';
      empty.style.display = 'block';
      return;
    }
    empty.style.display = 'none';

    grid.innerHTML = filtered.map((a, i) => `
      <article class="article-card" data-id="${a.id}" style="animation-delay: ${i * 0.05}s">
        <div class="card-tags">
          ${(a.tags || []).map(t => `<span class="card-tag" data-color="${getTagColor(t)}">${t}</span>`).join('')}
        </div>
        <h3 class="card-title">${escapeHtml(a.title)}</h3>
        <p class="card-summary">${escapeHtml(a.summary)}</p>
        <div class="card-footer">
          <span class="card-author">${escapeHtml(a.author || '匿名')}</span>
          <span class="card-date">${formatDate(a.date)}</span>
        </div>
      </article>
    `).join('');

    // Bind card clicks
    grid.querySelectorAll('.article-card').forEach(card => {
      card.addEventListener('click', () => {
        const article = articles.find(a => a.id === card.dataset.id);
        if (article) openModal(article);
      });
    });
  }

  // ── Modal ──
  function openModal(article) {
    document.getElementById('modalTitle').textContent = article.title;
    document.getElementById('modalMeta').innerHTML =
      `<span>${article.author || '匿名'}</span><span>${formatDate(article.date)}</span>` +
      (article.source ? `<a href="${escapeHtml(article.source)}" target="_blank" rel="noopener" style="color:var(--accent)">原文链接</a>` : '');
    document.getElementById('modalTags').innerHTML =
      (article.tags || []).map(t => `<span class="card-tag" data-color="${getTagColor(t)}">${t}</span>`).join('');

    // Render content: support simple paragraph breaks
    const content = (article.content || article.summary || '').replace(/\n/g, '\n\n');
    document.getElementById('modalBody').innerHTML = content.split('\n\n')
      .filter(p => p.trim())
      .map(p => `<p>${escapeHtml(p.trim())}</p>`)
      .join('');

    const overlay = document.getElementById('modalOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
  }

  // ── Theme ──
  function initTheme() {
    const saved = localStorage.getItem('theme');
    const prefer = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.dataset.theme = saved || prefer;
  }

  function toggleTheme() {
    const current = document.documentElement.dataset.theme;
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('theme', next);
  }

  // ── Helpers ──
  function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${mm}-${dd}`;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Event Bindings ──
  function bindEvents() {
    // Search
    document.getElementById('searchInput').addEventListener('input', (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      renderCards();
    });

    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);

    // Modal close
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) closeModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });
  }

  // ── Init ──
  function init() {
    initTheme();
    bindEvents();
    loadArticles();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
