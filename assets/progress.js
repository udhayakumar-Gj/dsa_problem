// Solved tracking and "random problem". Solved state lives in this browser's localStorage
// (key dsa-progress) because the site is static; Export / Import on the Topics page moves it
// between browsers or devices. Exposes window.dsaProgress for search.js.
(function () {
  var KEY = 'dsa-progress', HIDE_KEY = 'dsa-hide-done';
  var body = document.body;
  var base = body.getAttribute('data-base') || '';
  var indexUrl = body.getAttribute('data-index') || (base + '/assets/search-index.json');

  // ---------- storage ----------
  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      var d = raw ? JSON.parse(raw) : null;
      if (d && d.done && typeof d.done === 'object') return d;
    } catch (e) { /* unavailable or corrupt: start empty */ }
    return { v: 1, done: {} };
  }
  var store = load();
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { /* private mode: keep in memory */ }
  }
  function isDone(id) { return Object.prototype.hasOwnProperty.call(store.done, String(id)); }
  function setDone(id, on) {
    id = String(id);
    if (on) store.done[id] = new Date().toISOString().slice(0, 10);
    else delete store.done[id];
    save();
    document.dispatchEvent(new CustomEvent('dsa-progress', { detail: { id: id, done: !!on } }));
  }
  function doneCount() { return Object.keys(store.done).length; }
  function pref(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key) === '1';
      localStorage.setItem(key, value ? '1' : '0');
    } catch (e) { return false; }
  }
  window.dsaProgress = { isDone: isDone, setDone: setDone, count: doneCount, all: function () { return store.done; } };

  // ---------- problem index (for random picks and totals) ----------
  var indexP = null;
  function problems() {
    if (!indexP) indexP = fetch(indexUrl).then(function (r) { return r.json(); });
    return indexP;
  }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
  function articleUrl(id) { return base + '/p/' + id + '.html'; }
  function randomFrom(ids, exclude) {
    var pool = ids.filter(function (id) { return String(id) !== String(exclude) && !isDone(id); });
    if (!pool.length) pool = ids.filter(function (id) { return String(id) !== String(exclude); });
    return pool.length ? pick(pool) : null;
  }
  // header link: a random unsolved problem from the whole sheet (any page)
  Array.prototype.forEach.call(document.querySelectorAll('.nav-random'), function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      a.classList.add('busy');
      problems().then(function (list) {
        var id = randomFrom(list.map(function (p) { return p.id; }), body.getAttribute('data-problem-id'));
        if (id != null) location.href = articleUrl(id);
      }).catch(function () { a.classList.remove('busy'); });
    });
  });

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function plural(n, word) { return n + ' ' + (n === 1 ? word : word + 's'); }

  // ---------- table pages: Done column, progress line, hide-done, random from this page ----------
  var rows = Array.prototype.slice.call(document.querySelectorAll('.prob-table tbody tr[data-id]'));
  var track = document.querySelector('.track-table');
  if (rows.length && track) {
    var text = track.querySelector('.track-text'), bar = track.querySelector('.bar span');
    var hide = track.querySelector('.hide-done'), shuffle = track.querySelector('.shuffle');
    var search = document.getElementById('problem-search');

    function paintRow(tr) {
      var on = isDone(tr.getAttribute('data-id'));
      tr.classList.toggle('done', on);
      var box = tr.querySelector('input.done-box');
      if (box) box.checked = on;
    }
    function summary() {
      var n = rows.filter(function (tr) { return isDone(tr.getAttribute('data-id')); }).length;
      text.textContent = n + ' of ' + plural(rows.length, 'problem') + ' done' + (n === rows.length ? ' 🎉' : '');
      if (bar) bar.style.width = Math.round(100 * n / rows.length) + '%';
    }
    function refilter() { if (search) search.dispatchEvent(new Event('input')); }

    rows.forEach(function (tr) {
      paintRow(tr);
      var box = tr.querySelector('input.done-box');
      if (!box) return;
      box.addEventListener('change', function () {
        setDone(tr.getAttribute('data-id'), box.checked);
        paintRow(tr); summary(); refilter();
      });
    });
    summary();

    if (hide) {
      var on = pref(HIDE_KEY);
      hide.checked = on;
      body.classList.toggle('hide-done', on);
      hide.addEventListener('change', function () {
        body.classList.toggle('hide-done', hide.checked);
        pref(HIDE_KEY, hide.checked);
        refilter();
      });
    }
    if (shuffle) {
      shuffle.addEventListener('click', function () {
        // among the rows the search box currently shows, unsolved first
        var visible = rows.filter(function (tr) { return !tr.hidden; });
        var ids = (visible.length ? visible : rows).map(function (tr) { return tr.getAttribute('data-id'); });
        var id = randomFrom(ids, null);
        if (id != null) location.href = articleUrl(id);
      });
    }
  }

  // ---------- Topics page: overall progress, per-topic counts, export / import / reset ----------
  var home = document.querySelector('.track-index');
  if (home) {
    var htext = home.querySelector('.track-text'), hbar = home.querySelector('.bar span');
    var topicCounts = home.querySelector('.topic-list') || document.querySelector('.topic-list');
    function slug(s) { return String(s).toLowerCase().replace(/['’]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }
    function render(list) {
      var n = list.filter(function (p) { return isDone(p.id); }).length;
      htext.textContent = n ? 'You have solved ' + n + ' of ' + plural(list.length, 'problem') + ' (' + Math.round(100 * n / list.length) + '%).'
        : 'Nothing marked done yet. Tick a problem in any table, or press "Mark as done" on an article.';
      if (hbar) hbar.style.width = Math.round(100 * n / list.length) + '%';
      var per = {};
      list.forEach(function (p) { if (isDone(p.id)) per[slug(p.p)] = (per[slug(p.p)] || 0) + 1; });
      Array.prototype.forEach.call(document.querySelectorAll('.topic-list li'), function (li) {
        var a = li.querySelector('a[href]'), c = li.querySelector('.count');
        if (!a || !c) return;
        var m = a.getAttribute('href').match(/\/topics\/([^/]+)\.html/);
        var k = m ? per[m[1]] || 0 : 0;
        var tag = c.querySelector('.done-count');
        if (!tag) { tag = el('span', 'done-count'); c.appendChild(tag); }
        tag.textContent = k ? ' · ' + k + ' done' : '';
      });
    }
    problems().then(render).catch(function () { htext.textContent = 'Progress unavailable (could not load the problem index).'; });

    var exp = home.querySelector('.export'), imp = home.querySelector('.import'), reset = home.querySelector('.reset');
    if (exp) exp.addEventListener('click', function () {
      var blob = new Blob([JSON.stringify(store, null, 1)], { type: 'application/json' });
      var a = el('a'); a.href = URL.createObjectURL(blob);
      a.download = 'dsa-progress-' + new Date().toISOString().slice(0, 10) + '.json';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
    if (imp) imp.addEventListener('change', function () {
      var f = imp.files && imp.files[0];
      if (!f) return;
      var rd = new FileReader();
      rd.onload = function () {
        try {
          var d = JSON.parse(rd.result), src = d && d.done ? d.done : d;
          if (!src || typeof src !== 'object') throw new Error('not a progress file');
          var added = 0;
          Object.keys(src).forEach(function (id) {
            if (/^\d+$/.test(id) && !isDone(id)) { store.done[id] = String(src[id]).slice(0, 10); added++; }
          });
          save(); problems().then(render);
          alert('Imported ' + plural(added, 'new solved problem') + ' (merged with what was already here).');
        } catch (e) { alert('That file is not a progress export from this site.'); }
        imp.value = '';
      };
      rd.readAsText(f);
    });
    if (reset) reset.addEventListener('click', function () {
      if (!doneCount()) return;
      if (confirm('Clear all ' + plural(doneCount(), 'solved mark') + ' stored in this browser? Export first if you want a backup.')) {
        store.done = {}; save(); problems().then(render);
      }
    });
  }

  // ---------- article page: Mark as done ----------
  var toggle = document.querySelector('.done-toggle');
  if (toggle) {
    var pid = toggle.getAttribute('data-id');
    function paint() {
      var on = isDone(pid);
      toggle.classList.toggle('is-done', on);
      toggle.textContent = on ? '✓ Done' : 'Mark as done';
      toggle.setAttribute('aria-pressed', on ? 'true' : 'false');
      toggle.title = on ? 'Solved on ' + store.done[pid] + '. Click to unmark.' : 'Remember that you solved this problem (stored in this browser)';
    }
    paint();
    toggle.addEventListener('click', function () { setDone(pid, !isDone(pid)); paint(); });
  }
})();
