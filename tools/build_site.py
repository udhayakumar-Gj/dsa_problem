#!/usr/bin/env python3
"""Generate index.md, all.md and topics/*.md from _data/problems.json and the articles present in p/.
Also stamps prev/next navigation into each article's front matter. Run before every commit."""
import json, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = json.load(open(os.path.join(ROOT, '_data', 'problems.json'), encoding='utf-8'))

def slugify(s):
    s = re.sub(r"['’]", '', s.lower())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

import subprocess
def _published_ids():
    """Articles count as written only once they are tracked or staged in git, so pages for
    batches still being drafted never appear in the index."""
    try:
        out = subprocess.run(['git', 'ls-files', '--cached', 'p/'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return None
    return {int(os.path.basename(f)[:-3]) for f in out.split() if os.path.basename(f)[:-3].isdigit()}
_PUB = _published_ids()
def written(p):
    exists = os.path.exists(os.path.join(ROOT, 'p', f"{p['id']}.md"))
    return exists and (_PUB is None or p['id'] in _PUB)

by_topic = collections.OrderedDict()
for p in problems:
    by_topic.setdefault(p['topic'], []).append(p)

done_total = sum(1 for p in problems if written(p))
os.makedirs(os.path.join(ROOT, 'topics'), exist_ok=True)
# drop topic pages for topics that no longer exist (e.g. after merging)
for f in os.listdir(os.path.join(ROOT, 'topics')):
    if f.endswith('.md'): os.remove(os.path.join(ROOT, 'topics', f))

import html
# Solved problems, synced from the user's takeUforward sheet by tools/sync_tuf.py (static, committed).
_solved_path = os.path.join(ROOT, '_data', 'solved.json')
_solved_doc = json.load(open(_solved_path, encoding='utf-8')) if os.path.exists(_solved_path) else {}
SOLVED = {int(i) for i in _solved_doc.get('ids', [])}
SYNCED = _solved_doc.get('synced') or None
def solved(p): return p['id'] in SOLVED
SOLVED_TITLE = f'Solved on takeUforward (synced {SYNCED})' if SYNCED else 'Solved on takeUforward'
SHEET_LABEL = {'a2z': 'A2Z', 'sde': 'SDE', 'blind75': 'B75'}
SHEET_WORDS = {'a2z': 'a2z', 'sde': 'sde', 'blind75': 'b75 blind 75 blind75'}

FM_RE = re.compile(r'^---\n(.*?)\n---\n', re.S)
_LINKS = {}
def article_links(p):
    """Practice links from the article's front matter (the article is the source of truth):
    leetcode: <url>, gfg: <url>, leetcode_premium: true (the LeetCode problem is Premium-locked)."""
    if p['id'] in _LINKS: return _LINKS[p['id']]
    out = {}
    path = os.path.join(ROOT, 'p', f"{p['id']}.md")
    if os.path.exists(path):
        m = FM_RE.match(open(path, encoding='utf-8').read())
        fm = m.group(1) if m else ''
        for k in ('leetcode', 'gfg', 'practice'):
            mm = re.search(rf'^{k}:\s*(\S+)', fm, re.M)
            if mm: out[k] = mm.group(1)
        mm = re.search(r'^practice_site:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
        if mm: out['practice_site'] = mm.group(1)
        if re.search(r'^leetcode_premium:\s*true', fm, re.M): out['premium'] = True
    _LINKS[p['id']] = out
    return out

def link_cell(l):
    """The Problem link column: LeetCode when the problem is on LeetCode, GeeksforGeeks otherwise
    (both when both are set, e.g. a Premium LeetCode problem with a free GFG twin), and `practice:`
    (another judge such as Code360 or TUF+, labelled by `practice_site:`) when neither hosts the problem."""
    e = html.escape
    parts = []
    if l.get('leetcode'):
        lock = ' \U0001F512' if l.get('premium') else ''
        title = ' title="LeetCode Premium problem"' if l.get('premium') else ''
        parts.append(f'<a href="{e(l["leetcode"])}" target="_blank" rel="noopener"{title}>LeetCode{lock} \u2197</a>')
    if l.get('gfg'):
        parts.append(f'<a href="{e(l["gfg"])}" target="_blank" rel="noopener">GFG \u2197</a>')
    if l.get('practice'):
        parts.append(f'<a href="{e(l["practice"])}" target="_blank" rel="noopener">{e(l.get("practice_site") or "Practice")} \u2197</a>')
    return ' \u00b7 '.join(parts) if parts else '<span class="none" title="No practice problem for this row (theory, or no judge hosts it)">\u2014</span>'

def link_words(l):
    w = []
    if l.get('leetcode'): w += ['leetcode', 'lc'] + (['premium'] if l.get('premium') else [])
    if l.get('gfg'): w += ['gfg', 'geeksforgeeks']
    if l.get('practice'): w += ['practice', l.get('practice_site', '')]
    return ' '.join(w)

def status_words(p): return 'solved done' if solved(p) else 'unsolved todo pending'

def norm(*parts):
    """Lower-case, drop apostrophes, everything else non-alphanumeric becomes a space (mirrors search.js)."""
    t = ' '.join(str(x) for x in parts if x).lower()
    t = re.sub(r"['\u2019]", '', t)
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()

# the sheets misspell a few names; index the usual spelling too so either one finds the problem
SPELLINGS = {'djisktra': 'dijkstra', 'paranthesis': 'parenthesis parentheses', 'parentheses': 'parenthesis', 'parenthesis': 'parentheses'}

def name_text(p):
    n = norm(p['title'], ' '.join(p['aliases']))
    extra = [v for k, v in SPELLINGS.items() if k in n and v not in n]
    squashed = n.replace(' ', '')            # lets "nqueen" or "lrucache" match
    return ' '.join([n] + extra + [squashed])

def search_text(p):
    return norm(p['id'], name_text(p), p['topic'], p['section'], p['difficulty'],
                ' '.join(SHEET_WORDS[s] for s in p['sheets']), link_words(article_links(p)), status_words(p))

def row(p):
    e = html.escape
    cls = '' if written(p) else ' class="todo"'
    if written(p):
        title = f'<a href="{{{{ "/p/{p["id"]}.html" | relative_url }}}}" target="_blank" rel="noopener">{e(p["title"])}</a>'
    else:
        title = f'{e(p["title"])} <small>(coming soon)</small>'
    sheets = ' '.join(SHEET_LABEL[s] for s in p['sheets'])
    if solved(p): cls = (cls[:-1] + ' done"') if cls else ' class="done"'
    done = (f'<td class="done-cell" title="{SOLVED_TITLE}">\u2713</td>' if solved(p) else '<td class="done-cell"></td>')
    return (f'<tr{cls} data-id="{p["id"]}" data-difficulty="{p["difficulty"].lower()}" data-search="{e(search_text(p))}"><td>{p["id"]}</td><td>{title}</td>'
            f'<td><span class="badge badge-{p["difficulty"].lower()}">{p["difficulty"]}</span></td>'
            f'<td>{e(p["section"])}</td><td>{sheets}</td><td class="plink">{link_cell(article_links(p))}</td>{done}</tr>')

def search_box(mode, placeholder, extra=''):
    return (f'<div class="search" data-mode="{mode}"{extra}>'
            f'<input id="problem-search" type="search" placeholder="{placeholder}" aria-label="Search problems" autocomplete="off" spellcheck="false">'
            f'<p class="search-status" aria-live="polite"></p></div>')

SEARCH_SCRIPT = '<script src="{{ \'/assets/search.js\' | relative_url }}?v={{ site.time | date: \'%s\' }}" defer></script>'

def _pct(n, total): return round(100 * n / total) if total else 0

DIFFS = ('Easy', 'Medium', 'Hard')
def difficulty_chips(ps):
    """All / Easy / Medium / Hard buttons with counts; search.js applies them on top of the text filter."""
    counts = {d: sum(1 for p in ps if p['difficulty'] == d) for d in DIFFS}
    chips = [f'<button type="button" class="chip is-active" data-difficulty="" aria-pressed="true">All <small>{len(ps)}</small></button>']
    for d in DIFFS:
        dis = ' disabled' if not counts[d] else ''
        chips.append(f'<button type="button" class="chip chip-{d.lower()}" data-difficulty="{d.lower()}" aria-pressed="false"{dis}>{d} <small>{counts[d]}</small></button>')
    return '<div class="filters" role="group" aria-label="Filter by difficulty">' + ''.join(chips) + '</div>'

def track_table(ps):
    """Static progress line under the search box of a table page: solved count, hide-solved toggle, random pick."""
    n = sum(1 for p in ps if solved(p))
    note = f' <span class="track-hint">Synced from takeUforward {SYNCED}.</span>' if SYNCED else ''
    party = ' \U0001F389' if ps and n == len(ps) else ''
    dis_unsolved = ' disabled title="Everything here is solved"' if ps and n == len(ps) else ' title="Open a random unsolved problem from the rows shown"'
    dis_solved = ' disabled title="Nothing solved here yet"' if n == 0 else ' title="Revise: open a random problem you have already solved, from the rows shown"'
    return (f'<div class="track track-table"><span class="track-text">{n} of {len(ps)} solved{party}</span>{note}'
            '<label><input type="checkbox" class="hide-done"> Hide solved</label>'
            f'<button type="button" class="shuffle" data-mode="unsolved"{dis_unsolved}>\U0001F3B2 Random unsolved</button>'
            f'<button type="button" class="shuffle shuffle-solved" data-mode="solved"{dis_solved}>\U0001F501 Random solved</button>'
            f'<div class="bar"><span style="width:{_pct(n, len(ps))}%"></span></div></div>')

def track_index():
    n = len([p for p in problems if solved(p)])
    when = f' Synced from your takeUforward sheet on {SYNCED}; run <code>tools/sync_tuf.py</code> to refresh.' if SYNCED \
        else ' Nothing synced yet: run <code>tools/sync_tuf.py</code> to pull your takeUforward progress.'
    dis_solved = ' disabled' if n == 0 else ''
    return (f'<div class="track track-index"><span class="track-text">You have solved {n} of {len(problems)} problems ({_pct(n, len(problems))}%).{when}</span>'
            '<button type="button" class="shuffle nav-random" data-mode="unsolved" title="Open a random unsolved problem">\U0001F3B2 Random unsolved</button>'
            f'<button type="button" class="shuffle shuffle-solved nav-random" data-mode="solved"{dis_solved} title="Revise: open a random problem you have already solved">\U0001F501 Random solved</button>'
            f'<div class="bar"><span style="width:{_pct(n, len(problems))}%"></span></div></div>')

TABLE_HEAD = '<table class="prob-table"><thead><tr><th>ID</th><th>Problem</th><th>Difficulty</th><th>Section</th><th>Sheets</th><th class="plink">Problem link</th><th title="Solved on takeUforward (tools/sync_tuf.py)">Solved</th></tr></thead><tbody>'

# index.md
pct = round(100 * done_total / len(problems))
lines = ['---', 'title: Topics', 'permalink: /', '---',
         f'<p>{len(problems)} problems from Striver\'s A2Z, SDE and Blind 75 sheets, {done_total} written up ({pct}%). Every article has a brute-force to optimal walkthrough with Java code that compiles and passes its own tests, and links to the judge that hosts the problem.</p>',
         track_index(),
         search_box('index', f'Search {len(problems)} problems by name, topic or TUF ID',
                    ' data-index="{{ \'/assets/search-index.json\' | relative_url }}" data-all="{{ \'/all.html\' | relative_url }}"'),
         difficulty_chips(problems),
         '<ul class="search-results" hidden></ul>',
         '<ul class="topic-list">']
for topic, ps in by_topic.items():
    d = sum(1 for p in ps if written(p)); s = sum(1 for p in ps if solved(p))
    extra = f' <span class="done-count">\u00b7 {s} solved</span>' if s else ''
    lines.append(f'<li><a href="{{{{ "/topics/{slugify(topic)}.html" | relative_url }}}}">{topic}</a><span class="count">{d} / {len(ps)} written{extra}</span></li>')
lines.append('</ul>')
lines.append(SEARCH_SCRIPT)
open(os.path.join(ROOT, 'index.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

# all.md
lines = ['---', 'title: All problems', '---', f'<p>All {len(problems)} problems in sheet order, keyed by TUF ID.</p>',
         search_box('table', 'Filter by name, topic, section or TUF ID'), difficulty_chips(problems), track_table(problems), TABLE_HEAD]
lines += [row(p) for p in problems]
lines.append('</tbody></table>')
lines.append(SEARCH_SCRIPT)
open(os.path.join(ROOT, 'all.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

# topics/*.md
for topic, ps in by_topic.items():
    lines = ['---', f'title: "{topic}"', '---', f'<p><a href="{{{{ "/" | relative_url }}}}">← All topics</a></p>',
             search_box('table', f'Filter {len(ps)} {html.escape(topic)} problems'), difficulty_chips(ps), track_table(ps)]
    sections = collections.OrderedDict()
    for p in ps:
        sections.setdefault(p['section'], []).append(p)
    for sec, sp in sections.items():
        if sec:
            lines.append(f'<h2>{sec}</h2>')
        lines.append(TABLE_HEAD)
        lines += [row(p) for p in sp]
        lines.append('</tbody></table>')
    lines.append(SEARCH_SCRIPT)
    open(os.path.join(ROOT, 'topics', f'{slugify(topic)}.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

# assets/search-index.json: what the Topics page searches
index = [{'id': p['id'], 't': p['title'], 'd': p['difficulty'], 'p': p['topic'], 's': p['section'],
          'h': [SHEET_LABEL[x] for x in p['sheets']], 'n': name_text(p), 'q': search_text(p),
          'l': {k: v for k, v in article_links(p).items() if k in ('leetcode', 'gfg', 'practice', 'practice_site')},
          'done': solved(p)}
         for p in problems if written(p)]
with open(os.path.join(ROOT, 'assets', 'search-index.json'), 'w', encoding='utf-8') as f:
    json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

# prev/next stamping for written articles (in global sheet order)
written_list = [p for p in problems if written(p)]
for i, p in enumerate(written_list):
    path = os.path.join(ROOT, 'p', f"{p['id']}.md")
    txt = open(path, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n', txt, re.S)
    if not m:
        print('WARN no front matter:', path); continue
    fm = re.sub(r'^(prev_id|prev_title|next_id|next_title):.*\n?', '', m.group(1) + '\n', flags=re.M).rstrip('\n')
    extra = []
    if i > 0:
        q = written_list[i-1]; extra += [f'prev_id: {q["id"]}', f'prev_title: "{q["title"].replace(chr(34), "")}"']
    if i < len(written_list) - 1:
        q = written_list[i+1]; extra += [f'next_id: {q["id"]}', f'next_title: "{q["title"].replace(chr(34), "")}"']
    new = '---\n' + fm + ('\n' + '\n'.join(extra) if extra else '') + '\n---\n' + txt[m.end():]
    if new != txt:
        open(path, 'w', encoding='utf-8').write(new)

print(f'index: {len(by_topic)} topics, {done_total}/{len(problems)} articles written')
