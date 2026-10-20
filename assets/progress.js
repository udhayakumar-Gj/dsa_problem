// Random problem + "hide solved". Solved state is static: tools/sync_tuf.py writes _data/solved.json from the
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
  // unsolved first; when everything is solved, anything but the current problem
  function randomId(items, exclude) {
    var pool = items.filter(function (x) { return !x.done && String(x.id) !== String(exclude); });
    if (!pool.length) pool = items.filter(function (x) { return String(x.id) !== String(exclude); });
    return pool.length ? pick(pool).id : null;
  }

  var indexP = null;
  function problems() {
    if (!indexP) indexP = fetch(indexUrl).then(function (r) { return r.json(); });
    return indexP;
  }

  // header link and the Topics-page button: random unsolved problem from the whole sheet
  Array.prototype.forEach.call(document.querySelectorAll('.nav-random'), function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      a.classList.add('busy');
      problems().then(function (list) {
        var id = randomId(list, body.getAttribute('data-problem-id'));
        if (id != null) location.href = articleUrl(id); else a.classList.remove('busy');
      }).catch(function () { a.classList.remove('busy'); });
    });
  });

  // table pages: random from the rows currently shown, and the hide-solved toggle
  var rows = Array.prototype.slice.call(document.querySelectorAll('.prob-table tbody tr[data-id]'));
  var track = document.querySelector('.track-table');
  if (!rows.length || !track) return;
  var search = document.getElementById('problem-search');
  function refilter() { if (search) search.dispatchEvent(new Event('input')); }

  var shuffle = track.querySelector('.shuffle');
  if (shuffle) shuffle.addEventListener('click', function () {
    var visible = rows.filter(function (tr) { return !tr.hidden; });
    var items = (visible.length ? visible : rows).map(function (tr) {
      return { id: tr.getAttribute('data-id'), done: tr.classList.contains('done') };
    });
    var id = randomId(items, null);
    if (id != null) location.href = articleUrl(id);
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
