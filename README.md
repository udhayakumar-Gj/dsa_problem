# DSA Java Articles

Explanations and **Java** solutions for every problem in Striver's A2Z DSA sheet, the SDE sheet and Blind 75
(583 unique problems). Each article walks from brute force to the optimal approach with code, complexity and pitfalls.

Site: https://udhayakumar-gj.github.io/dsa_problem/

Forked from [manoshrinivasnm-glitch/dsa-java-articles](https://github.com/manoshrinivasnm-glitch/dsa-java-articles),
which wrote the articles. This copy adds a **Problem link** column to every problem table: the LeetCode problem when
the question is on LeetCode, otherwise the GeeksforGeeks practice problem, otherwise another judge that hosts it
(Code360, TUF+...), so each row jumps straight to somewhere you can solve it.

## How the pieces fit

| Path | What it is |
|---|---|
| `p/<id>.md` | One article per problem, named by the sheet's TUF ID. Rendered at `/p/<id>.html`. Front matter holds the practice links: `leetcode:` and/or `gfg:` (plus `leetcode_premium: true` when the LeetCode problem is Premium-locked), or `practice:` + `practice_site:` for another judge when neither hosts the problem. |
| `java/P<id>_<Name>.java` | All approaches for that problem plus a `main` with assertions. |
| `_data/problems.json` | Master list of the 583 problems (title, difficulty, topic, which sheets). |
| `tools/build_site.py` | Regenerates `index.md`, `all.md`, `topics/*.md` (including the Problem link column, read from each article's front matter) and prev/next links. Run before committing. |
| `tools/check_java.sh` | Compiles every Java file and runs its tests. Also runs in GitHub Actions on every push. |
| `ARTICLE_GUIDE.md` | The writing and coding standard every article follows. |

## Solved status (synced from takeUforward)

Solved marks are **static and committed**: `_data/solved.json` lists the TUF ids you have solved, and
`tools/build_site.py` renders them as the **Solved** column (✓), the per-page "n of m solved" lines, the per-topic
counts on the Topics page and a "✓ Solved" pill on the article. Nothing is kept in the browser.

The list comes from your own takeUforward prep-hub sheet, where problem ids are the same TUF ids this repo uses:

```
tools/sync_tuf.py --cookie "<Cookie header of a logged-in takeuforward.org request>"   # pull and merge
tools/sync_tuf.py --from-json progress.json    # same, from a saved API response
tools/sync_tuf.py --ids 38,43  /  --unsolve 38  /  --clear  /  --show
```

Then commit `_data/solved.json` and the regenerated pages. Table pages can **Hide solved** rows.

Two pickers: **🎲 Random** opens a random *unsolved* problem and **🔁 Revise** a random *solved* one. Both exist as
header links (whole sheet) and as buttons on the Topics page (whole sheet) and on topic / All-problems pages
(the rows currently shown).

## Linking from the progress sheet

Every page URL is derived from the TUF ID, so a single formula fixes the whole Resource column.
With the TUF ID in column `M` (A2Z tab) or `K` (SDE and Blind 75 tabs):

```
=HYPERLINK("https://udhayakumar-gj.github.io/dsa_problem/p/"&M2&".html","Article")
```

## Verify locally (optional)

Needs any JDK 17+ on the PATH:

```
tools/check_java.sh            # all solutions
tools/check_java.sh P37_TwoSum # one solution
```

`tools/check_links.py` checks every `leetcode:` / `gfg:` front-matter link against the live sites
(LeetCode GraphQL, GFG page titles) and reports dead or Premium problems.

## Preview the site locally

Needs Ruby 3+ with the `jekyll`, `jekyll-seo-tag`, `kramdown-parser-gfm` and `webrick` gems (`gem install ...`):

```
python3 tools/build_site.py
jekyll serve --baseurl /dsa_problem   # then open http://127.0.0.1:4000/dsa_problem/
```

## Publishing

GitHub Pages serves the `main` branch from the repository root (Settings → Pages → Deploy from a branch → `main` / `/`).
