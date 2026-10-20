// Random unsolved / random solved (revision) + "hide solved". Solved state is static: tools/sync_tuf.py writes _data/solved.json from the
// user's takeUforward sheet and build_site.py renders it (tr.done, the Solved column, the counts, and `done` in
// search-index.json). The only thing kept in this browser is the hide-solved preference.
(function () {
  var HIDE_KEY = 'dsa-hide-solved';
  var body = document.body;
  var base = body.getAttribute('data-base') || '';
  var indexUrl = body.getAttribute('data-index') || (base + '/assets/search-index.json');

  function pref(value) {
    try {
      if (value === undefined) return localStorage.getItem(HIDE_KEY) === '1';
      localStorage.setItem(HIDE_KEY, value ? '1' : '0');
    } catch (e) { return false; }
  }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
  function articleUrl(id) { return base + '/p/' + id + '.html'; }
  // mode "unsolved" (default): an unsolved problem, or anything once everything is solved.
  // mode "solved": revision, a problem already solved; null when there is none.
  function randomId(items, exclude, mode) {
    var wantSolved = mode === 'solved';
    var pool = items.filter(function (x) { return !!x.done === wantSolved && String(x.id) !== String(exclude); });
    if (!pool.length && !wantSolved) pool = items.filter(function (x) { return String(x.id) !== String(exclude); });
    return pool.length ? pick(pool).id : null;
  }
  function modeOf(el) { return el.getAttribute('data-mode') === 'solved' ? 'solved' : 'unsolved'; }

  var indexP = null;
  function problems() {
    if (!indexP) indexP = fetch(indexUrl).then(function (r) { return r.json(); });
    return indexP;
  }

  // header links and the Topics-page buttons: random problem from the whole sheet
  Array.prototype.forEach.call(document.querySelectorAll('.nav-random'), function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      if (a.disabled) return;
      a.classList.add('busy');
      problems().then(function (list) {
        var id = randomId(list, body.getAttribute('data-problem-id'), modeOf(a));
        if (id != null) location.href = articleUrl(id);
        else { a.classList.remove('busy'); a.title = 'Nothing solved yet: sync your takeUforward progress first'; }
      }).catch(function () { a.classList.remove('busy'); });
    });
  });

  // table pages: random from the rows currently shown, and the hide-solved toggle
  var rows = Array.prototype.slice.call(document.querySelectorAll('.prob-table tbody tr[data-id]'));
  var track = document.querySelector('.track-table');
  if (!rows.length || !track) return;
  var search = document.getElementById('problem-search');
  function refilter() { if (search) search.dispatchEvent(new Event('input')); }

  function itemsOf(trs) {
    return trs.map(function (tr) { return { id: tr.getAttribute('data-id'), done: tr.classList.contains('done') }; });
  }
  Array.prototype.forEach.call(track.querySelectorAll('.shuffle'), function (btn) {
    btn.addEventListener('click', function () {
      var mode = modeOf(btn);
      // prefer the rows the search box currently shows; fall back to the whole page
      // (e.g. "Random solved" while solved rows are hidden)
      var visible = rows.filter(function (tr) { return !tr.hidden; });
      var id = randomId(itemsOf(visible), null, mode);
      if (id == null) id = randomId(itemsOf(rows), null, mode);
      if (id != null) location.href = articleUrl(id);
    });
  });

  var hide = track.querySelector('.hide-done');
  if (hide) {
    var on = pref();
    hide.checked = on;
    body.classList.toggle('hide-done', on);
    hide.addEventListener('change', function () {
      body.classList.toggle('hide-done', hide.checked);
      pref(hide.checked);
      refilter();
    });
    if (on) refilter();
  }
})();
