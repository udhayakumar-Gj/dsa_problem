#!/usr/bin/env python3
"""Check every practice link in the articles' front matter against the live sites.

  leetcode: <url>   -> LeetCode GraphQL: the slug must exist; reports Premium (isPaidOnly) problems
                       and flags articles whose leetcode_premium flag disagrees with LeetCode.
  gfg: <url>        -> the GFG page title must be "<Name> | Practice | GeeksforGeeks"
                       (GFG answers 200 with a generic title for unknown slugs, so status codes mean nothing).
  practice: <url>   -> any other judge (Code360, TUF+, ...): the page must load (HTTP 200) with an HTML <title>.

Usage: tools/check_links.py [--fix-premium] [ids...]     (no ids = every article)
  --fix-premium   write leetcode_premium: true/false into the front matter to match LeetCode.
Exit status 1 when any link is dead or malformed."""
import glob, json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json', 'Referer': 'https://leetcode.com'}
LC_RE = re.compile(r'^https://leetcode\.com/problems/([a-z0-9-]+)/$')
GFG_RE = re.compile(r'^https://www\.geeksforgeeks\.org/problems/([a-z0-9-]+)/\d+$')
FM_RE = re.compile(r'^---\n(.*?)\n---\n', re.S)


class _Redirect308(urllib.request.HTTPRedirectHandler):
    """GFG answers some problem URLs with 308, which urllib does not follow by default."""
    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_307

_opener = urllib.request.build_opener(_Redirect308)

def fetch(url, data=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            return _opener.open(req, timeout=30).read().decode('utf-8', 'replace')
        except Exception as e:                      # noqa: BLE001 - network flakiness, retry
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


_lc_cache = {}
def leetcode_question(slug):
    if slug not in _lc_cache:
        q = {'query': 'query q($s:String!){question(titleSlug:$s){questionFrontendId title isPaidOnly}}',
             'variables': {'s': slug}}
        _lc_cache[slug] = json.loads(fetch('https://leetcode.com/graphql', json.dumps(q).encode()))['data']['question']
    return _lc_cache[slug]


_gfg_cache = {}
def gfg_title(url):
    if url not in _gfg_cache:
        m = re.search(r'<title>([^<]*)</title>', fetch(url))
        t = m.group(1).strip() if m else ''
        _gfg_cache[url] = t if t.endswith('| Practice | GeeksforGeeks') else None
    return _gfg_cache[url]


def main(argv):
    fix = '--fix-premium' in argv
    ids = [int(a) for a in argv if a.isdigit()]
    files = [os.path.join(ROOT, 'p', f'{i}.md') for i in ids] if ids else sorted(glob.glob(os.path.join(ROOT, 'p', '*.md')))
    bad = 0; premium = []; checked = 0
    for path in files:
        pid = os.path.basename(path)[:-3]
        txt = open(path, encoding='utf-8').read()
        m = FM_RE.match(txt)
        if not m:
            continue
        fm = m.group(1)
        lc = re.search(r'^leetcode:\s*(\S+)', fm, re.M)
        gf = re.search(r'^gfg:\s*(\S+)', fm, re.M)
        flag = bool(re.search(r'^leetcode_premium:\s*true', fm, re.M))
        if lc:
            checked += 1
            mm = LC_RE.match(lc.group(1))
            if not mm:
                bad += 1; print(f'[{pid}] malformed leetcode url: {lc.group(1)}'); continue
            q = leetcode_question(mm.group(1))
            if not q:
                bad += 1; print(f'[{pid}] DEAD leetcode slug: {mm.group(1)}')
            else:
                if q['isPaidOnly']:
                    premium.append(pid)
                if q['isPaidOnly'] != flag:
                    print(f'[{pid}] leetcode_premium should be {str(q["isPaidOnly"]).lower()} ({q["title"]})')
                    if fix:
                        fm2 = re.sub(r'^leetcode_premium:.*\n', '', fm + '\n', flags=re.M).rstrip('\n')
                        if q['isPaidOnly']:
                            fm2 = re.sub(r'^(leetcode:.*)$', r'\1\nleetcode_premium: true', fm2, flags=re.M)
                        txt = '---\n' + fm2 + '\n---\n' + txt[m.end():]
                        open(path, 'w', encoding='utf-8').write(txt)
        if gf:
            checked += 1
            if not GFG_RE.match(gf.group(1)):
                bad += 1; print(f'[{pid}] malformed gfg url: {gf.group(1)}'); continue
            t = gfg_title(gf.group(1))
            if not t:
                bad += 1; print(f'[{pid}] DEAD gfg url: {gf.group(1)}')
        pr = re.search(r'^practice:\s*(\S+)', fm, re.M)
        if pr:
            checked += 1
            try:
                page = fetch(pr.group(1))
                if not re.search(r'<title>[^<]+</title>', page):
                    bad += 1; print(f'[{pid}] practice url has no <title>: {pr.group(1)}')
            except Exception as ex:                  # noqa: BLE001
                bad += 1; print(f'[{pid}] DEAD practice url: {pr.group(1)} ({ex})')
        if not lc and not gf and not pr:
            print(f'[{pid}] no practice link (theory row?)')
    print(f'checked {checked} links in {len(files)} articles: {bad} dead/malformed, {len(premium)} LeetCode Premium')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
