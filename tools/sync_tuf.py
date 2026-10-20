#!/usr/bin/env python3
"""Sync solved marks from the user's takeUforward (TUF) sheet into _data/solved.json, then rebuild the index pages.

TUF problem ids are the same numbers as this repo's p/<id>.md, so a problem marked solved on takeUforward's
prep-hub sheet marks the matching article here. The result is static (committed), not browser memory.

How TUF exposes it: the logged-in sheet page https://takeuforward.org/prep-hub/<sheet>?page=sheet embeds
"solvedProblemIds":[...] in its server-rendered payload. This tool reads that for the A2Z, SDE and Blind 75 sheets.

Usage:
  tools/sync_tuf.py --cookie "<Cookie header copied from a logged-in takeuforward.org request>"
  tools/sync_tuf.py --from-json progress.json       # output of the browser snippet below (or any JSON with ids)
  tools/sync_tuf.py --ids 38,43,41                  # add ids by hand
  tools/sync_tuf.py --unsolve 38                    # remove ids by hand
  tools/sync_tuf.py --clear                         # forget everything
  tools/sync_tuf.py --show                          # print the current list

Everything except --show rewrites _data/solved.json and runs tools/build_site.py.
Only ids that exist in _data/problems.json are kept; unknown ids are reported and dropped.

No cookie handy? In a logged-in takeuforward.org tab, run this in the DevTools console and save the printed JSON:
  (async()=>{const o={};for(const s of ['strivers-a2z-dsa-sheet','strivers-sde-sheet','blind-75']){const h=await fetch(
  '/prep-hub/'+s+'?page=sheet',{credentials:'include'}).then(r=>r.text());const m=h.replace(/\\"/g,'"').match(
  /"solvedProblemIds":\[([^\]]*)\]/);o[s]=m?m[1].split(',').filter(Boolean).map(Number):[]}console.log(JSON.stringify(o))})()
then: tools/sync_tuf.py --from-json that-file.json --replace"""
import argparse, datetime, json, os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '_data', 'solved.json')
KNOWN = {p['id']: p['title'] for p in json.load(open(os.path.join(ROOT, '_data', 'problems.json'), encoding='utf-8'))}

# TUF sheets whose problems this repo covers (prep-hub slugs); their ids are this repo's p/<id>.md
SHEETS = ['strivers-a2z-dsa-sheet', 'strivers-sde-sheet', 'blind-75']
SHEET_URL = 'https://takeuforward.org/prep-hub/{sheet}?page=sheet'
SOLVED_RE = re.compile(r'"solvedProblemIds":\[([^\]]*)\]')


def load():
    if os.path.exists(OUT):
        return json.load(open(OUT, encoding='utf-8'))
    return {'source': 'takeuforward.org prep-hub', 'synced': None, 'ids': []}


def extract_ids(obj, found=None):
    """Walk any JSON shape from TUF and collect ids of entries that look solved.
    Handles {"id": 38, "solved": true} / {"problem_id": 38, "status": "solved"} / plain lists of ids."""
    if found is None:
        found = set()
    if isinstance(obj, list):
        if obj and all(isinstance(x, (int, str)) and str(x).isdigit() for x in obj):
            found.update(int(x) for x in obj)
        else:
            for x in obj:
                extract_ids(x, found)
    elif isinstance(obj, dict):
        pid = None
        for k in ('id', 'problem_id', 'problemId', 'qid', 'question_id'):
            v = obj.get(k)
            if isinstance(v, (int, str)) and str(v).isdigit():
                pid = int(v); break
        status = obj.get('solved', obj.get('is_solved', obj.get('isSolved', obj.get('completed', obj.get('done')))))
        if status is None and isinstance(obj.get('status'), str):
            status = obj['status'].lower() in ('solved', 'done', 'completed', 'accepted')
        if pid is not None and status is True and obj.get('kind', 'problem') == 'problem':
            found.add(pid)
        for v in obj.values():
            if isinstance(v, (dict, list)):
                extract_ids(v, found)
    return found


def fetch_with_cookie(cookie):
    """Fetch each sheet page as the logged-in user and pull solvedProblemIds out of the embedded payload."""
    found = set()
    for sheet in SHEETS:
        req = urllib.request.Request(SHEET_URL.format(sheet=sheet),
                                     headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie, 'Accept': 'text/html'})
        try:
            html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
        except Exception as e:                      # noqa: BLE001
            print(f'  {sheet}: {e}'); continue
        m = SOLVED_RE.search(html.replace('\\"', '"'))
        if not m:
            print(f'  {sheet}: no solvedProblemIds in the page (cookie expired or not logged in?)'); continue
        ids = {int(x) for x in m.group(1).split(',') if x.strip().isdigit()}
        print(f'  {sheet}: {len(ids)} solved')
        found |= ids
    return found


def write(ids, note):
    doc = load()
    known = sorted(i for i in ids if i in KNOWN)
    unknown = sorted(i for i in ids if i not in KNOWN)
    doc['ids'] = known
    doc['synced'] = datetime.date.today().isoformat()
    doc['source'] = note
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), indent=1)
    print(f'solved: {len(known)} of {len(KNOWN)} problems written to _data/solved.json'
          + (f' ({len(unknown)} ids not in this repo ignored: {unknown[:10]}{"..." if len(unknown) > 10 else ""})' if unknown else ''))
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'build_site.py')], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cookie', help='Cookie header of a logged-in takeuforward.org session')
    ap.add_argument('--from-json', help='JSON file with TUF progress data (any shape with ids + solved flags)')
    ap.add_argument('--ids', help='comma-separated TUF ids to mark solved')
    ap.add_argument('--unsolve', help='comma-separated TUF ids to unmark')
    ap.add_argument('--replace', action='store_true', help='with --from-json/--cookie: replace the list instead of merging')
    ap.add_argument('--clear', action='store_true')
    ap.add_argument('--show', action='store_true')
    a = ap.parse_args()
    current = set(load().get('ids', []))

    if a.show or not any([a.cookie, a.from_json, a.ids, a.unsolve, a.clear]):
        doc = load()
        print(f"{len(doc['ids'])} solved (synced {doc.get('synced')}):")
        for i in doc['ids']:
            print(f'  {i:>5}  {KNOWN.get(i, "?")}')
        return
    if a.clear:
        write(set(), 'cleared'); return
    ids = set(current)
    if a.cookie:
        got = fetch_with_cookie(a.cookie)
        ids = got if a.replace else ids | got
    if a.from_json:
        got = extract_ids(json.load(open(a.from_json, encoding='utf-8')))
        print(f'  {a.from_json}: {len(got)} solved ids found')
        ids = got if a.replace else ids | got
    if a.ids:
        ids |= {int(x) for x in re.split(r'[,\s]+', a.ids.strip()) if x}
    if a.unsolve:
        ids -= {int(x) for x in re.split(r'[,\s]+', a.unsolve.strip()) if x}
    write(ids, "takeuforward.org prep-hub (Striver's A2Z / SDE / Blind 75 progress)")


if __name__ == '__main__':
    main()
