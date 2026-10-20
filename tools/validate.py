#!/usr/bin/env python3
"""Structural checks for articles + Java files (no compiler needed).
Usage: tools/validate.py [batch numbers...]   (no args = every problem that has an article)"""
import json, os, re, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = {p['id']: p for p in json.load(open(os.path.join(ROOT, '_data', 'problems.json'), encoding='utf-8'))}
REQUIRED_FM = ['title', 'id', 'difficulty', 'topic', 'section', 'sheets', 'java']
REQUIRED_H2 = ['## Problem']

ids = []
if len(sys.argv) > 1:
    for b in sys.argv[1:]:
        ids += [p['id'] for p in json.load(open(os.path.join(ROOT, 'tools', 'batches', f'{int(b):02d}.json'), encoding='utf-8'))]
else:
    ids = sorted(int(os.path.basename(f)[:-3]) for f in glob.glob(os.path.join(ROOT, 'p', '*.md')) if os.path.basename(f)[:-3].isdigit())

errors = 0
def err(pid, msg):
    global errors; errors += 1; print(f'  [{pid}] {msg}')

for pid in ids:
    p = problems.get(pid)
    art_path = os.path.join(ROOT, 'p', f'{pid}.md')
    if not os.path.exists(art_path):
        err(pid, 'article missing'); continue
    art = open(art_path, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n', art, re.S)
    if not m:
        err(pid, 'no front matter'); continue
    fm = m.group(1)
    for k in REQUIRED_FM:
        if not re.search(rf'^{k}:', fm, re.M): err(pid, f'front matter missing {k}')
    mid = re.search(r'^id:\s*(\d+)', fm, re.M)
    if mid and int(mid.group(1)) != pid: err(pid, f'front matter id {mid.group(1)} != file name')
    mj = re.search(r'^java:\s*(\S+)', fm, re.M)
    java_rel = mj.group(1) if mj else None
    if java_rel:
        jpath = os.path.join(ROOT, java_rel)
        if not os.path.exists(jpath):
            err(pid, f'java file missing: {java_rel}')
        else:
            jsrc = open(jpath, encoding='utf-8').read()
            cls = os.path.basename(java_rel)[:-5]
            if not re.search(rf'public\s+(final\s+)?class\s+{re.escape(cls)}\b', jsrc): err(pid, f'class name != file name ({cls})')
            if not re.match(rf'P{pid}_[A-Za-z0-9]+\.java$', os.path.basename(java_rel)): err(pid, f'java file name not P{pid}_<CamelName>.java')
            if 'static void main(' not in jsrc: err(pid, 'no main()')
            if f'OK {cls}' not in jsrc: err(pid, 'main does not print OK <ClassName>')
            if re.search(r'^package\s', jsrc, re.M): err(pid, 'package statement present')
            if re.search(r'^import\s+(?!java\.util)', jsrc, re.M): err(pid, 'import outside java.util')
            # code blocks must match java source (article code may be de-indented by 4 spaces)
            jnorm = re.sub(r'^    ', '', jsrc, flags=re.M)
            for blk in re.findall(r'```java\n(.*?)```', art, re.S):
                b = blk.strip('\n')
                if b and b not in jsrc and b not in jnorm:
                    first = b.split('\n')[0][:60]
                    err(pid, f'code block not found in java file: "{first}"')
    body = art[m.end():]
    h2s = re.findall(r'^## .+', body, re.M)
    if re.search(r'^## Approach', body, re.M):
        for h in REQUIRED_H2:
            if h not in body: err(pid, f'missing section {h}')
    elif len(h2s) < 3:
        err(pid, 'concept article with fewer than 3 sections')
    stripped = re.sub(r'{% raw %}.*?{% endraw %}', '', body, flags=re.S)
    stripped = re.sub(r'{{\s*"/p/\d+\.html"\s*\|\s*relative_url\s*}}', '', stripped)
    if re.search(r'{{|{%', stripped): err(pid, 'unescaped {{ or {% in article body')
    if re.search(r'@@|PLACEHOLDER|\bTODO\b', body): err(pid, 'leftover placeholder (@@ / PLACEHOLDER / TODO) in article')
    words = len(re.sub(r'```.*?```', '', body, flags=re.S).split())
    if words < 500: err(pid, f'article short ({words} words)')
    ml = re.search(r'^leetcode:\s*(\S+)', fm, re.M)
    if ml and not re.match(r'^https://leetcode\.com/problems/[a-z0-9-]+/$', ml.group(1)):
        err(pid, f'leetcode link not of the form https://leetcode.com/problems/<slug>/: {ml.group(1)}')
    mg = re.search(r'^gfg:\s*(\S+)', fm, re.M)
    if mg and not re.match(r'^https://www\.geeksforgeeks\.org/problems/[a-z0-9-]+/\d+$', mg.group(1)):
        err(pid, f'gfg link not of the form https://www.geeksforgeeks.org/problems/<slug>/1: {mg.group(1)}')
    mp = re.search(r'^practice:\s*(\S+)', fm, re.M)
    if mp and not re.match(r'^https://\S+$', mp.group(1)):
        err(pid, f'practice link must be an https URL: {mp.group(1)}')
    if mp and not re.search(r'^practice_site:\s*\S', fm, re.M):
        err(pid, 'practice: needs a practice_site: label (e.g. Code360, TUF+)')
    for key in ('topic', 'section'):
        mt = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', fm, re.M)
        if p and mt and mt.group(1) != p[key]: err(pid, f'{key} {mt.group(1)!r} differs from problems.json {p[key]!r}')
    if p and p['difficulty'] and not re.search(rf'^difficulty:\s*{p["difficulty"]}', fm, re.M): err(pid, 'difficulty differs from problems.json')

print(f'checked {len(ids)} problems, {errors} issue(s)')
sys.exit(1 if errors else 0)
