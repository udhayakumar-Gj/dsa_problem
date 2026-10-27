// Problem search. Two modes, chosen by <div class="search" data-mode="...">:
//   index: searches every problem (assets/search-index.json) and lists matches under the box.
//   table: filters the .prob-table rows already on the page (All problems, topic pages).
// Problem links open in a new tab. "/" focuses the box, Esc clears it.
(function () {
  var box = document.querySelector('.search');
  var input = document.getElementById('problem-search');
  if (!box || !input) return;
  var status = box.querySelector('.search-status');
  var mode = box.getAttribute('data-mode');

  function norm(s) {
    return String(s).toLowerCase().replace(/['’]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  }
  function tokens(q) { var n = norm(q); return n ? n.split(' ') : []; }
  function hasAll(hay, toks) {
    for (var i = 0; i < toks.length; i++) if (hay.indexOf(toks[i]) === -1) return false;
    return true;
  }
  function plural(n, word, many) { return n + ' ' + (n === 1 ? word : (many || word + 's')); }

  // ---- shared keyboard behaviour ----
  document.addEventListener('keydown', function (e) {
    var t = e.target, typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
    if (e.key === '/' && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) { e.preventDefault(); input.focus(); input.select(); }
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { input.value = ''; input.dispatchEvent(new Event('input')); }
  });

  // prefill from ?q= and ?d=
  var params = new URLSearchParams(location.search);
  if (params.get('q')) input.value = params.get('q');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.filters .chip'));
  var diff = '';
  function setDiff(d, silent) {
    diff = d || '';
    chips.forEach(function (c) {
      var on = (c.getAttribute('data-difficulty') || '') === diff;
      c.classList.toggle('is-active', on);
      c.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    if (!silent) input.dispatchEvent(new Event('input'));
  }
  chips.forEach(function (c) {
    c.addEventListener('click', function () { setDiff(c.getAttribute('data-difficulty') || ''); });
  });
  if (params.get('d') && chips.length) setDiff(params.get('d'), true);
  var DIFF_LABEL = { easy: 'Easy', medium: 'Medium', hard: 'Hard' };
  function syncUrl() {
    if (!history.replaceState) return;
    var u = new URL(location.href);
    if (input.value.trim()) u.searchParams.set('q', input.value.trim()); else u.searchParams.delete('q');
    if (diff) u.searchParams.set('d', diff); else u.searchParams.delete('d');
    history.replaceState(null, '', u.toString());
  }

  if (mode === 'table') {
    var rows = Array.prototype.slice.call(document.querySelectorAll('.prob-table tbody tr'));
    var tables = Array.prototype.slice.call(document.querySelectorAll('.prob-table'));
    var empty = document.createElement('p');
    empty.className = 'search-empty';
    empty.hidden = true;
    empty.textContent = 'No problems match. Try fewer or shorter words.';
    tables[tables.length - 1].insertAdjacentElement('afterend', empty);

    function filter() {
      var toks = tokens(input.value), shown = 0;
      var hideDone = document.body.classList.contains('hide-done');
      rows.forEach(function (r) {
        var ok = !toks.length || hasAll(r.getAttribute('data-search') || '', toks);
        if (ok && diff && r.getAttribute('data-difficulty') !== diff) ok = false;
        if (ok && hideDone && r.classList.contains('done')) ok = false;
        r.hidden = !ok;
        if (ok) shown++;
      });
      // on topic pages, hide a section (heading + table) when none of its rows match
      tables.forEach(function (t) {
        var any = t.querySelector('tbody tr:not([hidden])');
        t.hidden = !any;
        var h = t.previousElementSibling;
        if (h && h.tagName === 'H2') h.hidden = !any;
      });
      empty.hidden = shown > 0;
      var notes = [];
      if (diff) notes.push(DIFF_LABEL[diff] + ' only');
      if (hideDone) notes.push('solved hidden');
      status.textContent = (toks.length || hideDone || diff) ? 'Showing ' + shown + ' of ' + plural(rows.length, 'problem') + (notes.length ? ' (' + notes.join(', ') + ')' : '') : '';
      syncUrl();
    }
    input.addEventListener('input', filter);
    filter();
    return;
  }

  // ---- index mode ----
  var LIMIT = 50;
  var list = document.querySelector('.search-results');
  var data = null, loading = null;
  var base = (box.getAttribute('data-all') || '/all.html').replace(/all\.html$/, '');
  var allUrl = box.getAttribute('data-all');

  function load() {
    if (!loading) {
      loading = fetch(box.getAttribute('data-index')).then(function (r) { return r.json(); })
        .then(function (d) { data = d; return d; });
    }
    return loading;
  }

  function score(p, toks, q) {
    if (diff && String(p.d).toLowerCase() !== diff) return -1;
    if (!toks.length) return 0;                                                 // chip only: keep sheet order
    if (!hasAll(p.q, toks)) return -1;
    if (/^\d+$/.test(q) && String(p.id) === q) return 1000;
    var title = norm(p.t), s = 0;
    if (title === q) s += 500;
    else if (title.indexOf(q) === 0) s += 300;
    else if (p.n.indexOf(q) !== -1) s += 200;
    var words = p.n.split(' ');
    toks.forEach(function (t) {
      if (words.some(function (w) { return w.indexOf(t) === 0; })) s += 30;      // word starts with token
      else if (t.length > 2 && p.n.indexOf(t) !== -1) s += 15;                  // inside the name
      else s += 1;                                                              // only topic/section/sheet
    });
    return s;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function render() {
    var toks = tokens(input.value);
    syncUrl();
    if (!toks.length && !diff) { list.hidden = true; list.innerHTML = ''; status.textContent = ''; return; }
    if (!data) { status.textContent = 'Loading…'; load().then(render); return; }
    var q = toks.join(' ');
    var hits = [];
    data.forEach(function (p, i) { var s = score(p, toks, q); if (s >= 0) hits.push({ p: p, s: s, i: i }); });
    hits.sort(function (a, b) { return b.s - a.s || a.i - b.i; });

    list.innerHTML = '';
    hits.slice(0, LIMIT).forEach(function (h) {
      var p = h.p, li = el('li');
      if (p.done) li.className = 'done';
      var a = el('a', 'result-title', (p.done ? '✓ ' : '') + p.t);
      a.href = base + 'p/' + p.id + '.html';
      a.target = '_blank';
      a.rel = 'noopener';
      var badge = el('span', 'badge badge-' + p.d.toLowerCase(), p.d);
      var meta = el('span', 'result-meta', p.p + (p.s ? ' › ' + p.s : '') + ' · ' + p.h.join(' ') + ' · ID ' + p.id);
      li.appendChild(a); li.appendChild(badge);
      // practice links (same data as the Problem link column)
      var links = p.l || {};
      [['leetcode', 'LeetCode ↗'], ['gfg', 'GFG ↗'], ['practice', (links.practice_site || 'Practice') + ' ↗']].forEach(function (k) {
        if (!links[k[0]]) return;
        var pl = el('a', 'result-link', k[1]);
        pl.href = links[k[0]]; pl.target = '_blank'; pl.rel = 'noopener';
        li.appendChild(pl);
      });
      li.appendChild(meta);
      list.appendChild(li);
    });
    if (!hits.length) list.appendChild(el('li', 'search-empty', 'No problems match. Try fewer or shorter words.'));
    list.hidden = false;

    var msg = plural(hits.length, 'match', 'matches') + (diff ? ' (' + DIFF_LABEL[diff] + ' only)' : '');
    status.textContent = '';
    status.appendChild(document.createTextNode(msg));
    if (hits.length > LIMIT) {
      status.appendChild(document.createTextNode(', showing the first ' + LIMIT + '. '));
      var more = el('a', null, 'See all in All problems');
      var qs = new URLSearchParams();
      if (input.value.trim()) qs.set('q', input.value.trim());
      if (diff) qs.set('d', diff);
      more.href = allUrl + '?' + qs.toString();
      status.appendChild(more);
    }
  }

  input.addEventListener('input', render);
  input.addEventListener('focus', load, { once: true });
  chips.forEach(function (c) { c.addEventListener('mouseenter', load, { once: true }); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      var first = list.querySelector('a.result-title');
      if (first) { e.preventDefault(); window.open(first.href, '_blank', 'noopener'); }
    }
  });
  if (input.value || diff) render();
})();
