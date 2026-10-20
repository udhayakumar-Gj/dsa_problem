# dsa-java-articles — notes for future sessions

Udhayakumar's copy of `manoshrinivasnm-glitch/dsa-java-articles` (Jekyll site, 583 Striver A2Z/SDE/Blind-75 articles
with Java solutions). Hosted at https://udhayakumar-gj.github.io/dsa-java-articles/ once pushed; `origin` is
`udhayakumar-Gj/dsa-java-articles`, `upstream` is the original (merge from it with `git fetch upstream && git merge upstream/main`).

## What this fork adds (see README for the user-facing version)

- **Problem link column** on every table (after Sheets). Source of truth is each article's front matter:
  `leetcode:` (+ `leetcode_premium: true` when LeetCode locks it), `gfg:` (`/problems/<slug>/1` practice URL),
  `practice:` + `practice_site:` for any other judge (TUF+ `takeuforward.org/practice/dsa/<slug>`, Code360).
  Preference order LeetCode → GFG → other; both are shown when both are set. 26 pure-theory rows have none ("—").
- **Done tracking + 🎲 Random** in `assets/progress.js`: solved marks live in the browser's `localStorage`
  (`dsa-progress`), Export/Import/Reset on the Topics page, `Hide done` on table pages, "Mark as done" on articles.
  Static site, so there is no cross-device sync beyond export/import.
- `tools/check_links.py` live-checks every link (LeetCode GraphQL + GFG page titles; GFG returns 200 for bad slugs).

## Workflow

```
python3 tools/build_site.py      # regenerates index.md, all.md, topics/*.md, search-index.json, prev/next
python3 tools/validate.py        # structure + link-shape checks (0 issues expected)
python3 tools/check_links.py     # slow, hits the network; run after editing links
```

Local preview: Homebrew Ruby 4 + gems were installed for this; the binary is
`/opt/homebrew/lib/ruby/gems/4.0.0/bin/jekyll` (not on PATH). `jekyll serve --baseurl /dsa-java-articles` from the
repo root, then open http://localhost:4000/dsa-java-articles/. `_site/` is git-ignored.

GitHub Pages: branch `main`, folder `/ (root)`. `_config.yml` `url`/`baseurl`/`repo_url` are already set for this account.
