# dsa-java-articles — notes for future sessions

Udhayakumar's copy of `manoshrinivasnm-glitch/dsa-java-articles` (Jekyll site, 583 Striver A2Z/SDE/Blind-75 articles
with Java solutions). Hosted at https://udhayakumar-gj.github.io/dsa-java-articles/ once pushed; `origin` is
`udhayakumar-Gj/dsa-java-articles`, `upstream` is the original (merge from it with `git fetch upstream && git merge upstream/main`).

## What this fork adds (see README for the user-facing version)

- **Problem link column** on every table (after Sheets). Source of truth is each article's front matter:
  `leetcode:` (+ `leetcode_premium: true` when LeetCode locks it), `gfg:` (`/problems/<slug>/1` practice URL),
  `practice:` + `practice_site:` for any other judge (TUF+ `takeuforward.org/practice/dsa/<slug>`, Code360).
  Preference order LeetCode → GFG → other; both are shown when both are set. 26 pure-theory rows have none ("—").
- **Solved status is static**: `_data/solved.json` (`ids` = TUF ids, `synced` = date) is written by
  `tools/sync_tuf.py` from the user's takeUforward prep-hub sheet and rendered by `build_site.py` (row class `done`,
  Solved column, counts, `done` flag in `search-index.json`, "✓ Solved" pill via `site.data.solved.ids contains page.id`).
  The user explicitly did NOT want browser-memory (localStorage) tracking; `assets/progress.js` only does 🎲 Random
  (prefers unsolved) and the hide-solved toggle.
- **TUF sheet facts**: prep-hub pages (`takeuforward.org/prep-hub/strivers-a2z-dsa-sheet`) embed a tree whose problem
  nodes carry the TUF `id` (== our `p/<id>.md`) and `/practice/dsa/<slug>` hrefs; login is at
  `takeuforward.org/get-started?type=login`. When logged in, each sheet page
  (`/prep-hub/strivers-a2z-dsa-sheet|strivers-sde-sheet|blind-75?page=sheet`) embeds `"solvedProblemIds":[...]`
  in its server-rendered payload; `sync_tuf.py --cookie` reads that, and `--from-json` takes the output of the
  console snippet in the script's docstring. First sync on 2026-10-20: 199 solved (A2Z 188, SDE 117, Blind 75 35,
  overlapping), all 199 present in this repo. The user reads progress with Claude in Chrome (logged-in profile);
  the built-in browser pane is not logged in.
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
