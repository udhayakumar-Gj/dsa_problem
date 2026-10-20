# DSA Java Articles

Explanations and **Java** solutions for every problem in Striver's A2Z DSA sheet, the SDE sheet and Blind 75
(583 unique problems). Each article walks from brute force to the optimal approach with code, complexity and pitfalls.

Site: https://udhayakumar-gj.github.io/dsa-java-articles/

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

## Tracking what you have solved

Every table has a **Done** checkbox per problem and every article a **Mark as done** button. Solved marks are stored
in the browser's `localStorage` (the site is static, there is no server), so they persist on that browser and device.
The Topics page shows overall and per-topic counts and has **Export progress** / **Import** (a small JSON file) to move
marks between browsers or devices, plus **Reset**. Table pages can **Hide done** rows.

**🎲 Random** (header link, and the "Random problem" buttons) opens a problem you have not marked done: from the whole
sheet on the Topics page and in the header, from the current page's visible rows on topic / All-problems pages.

## Linking from the progress sheet

Every page URL is derived from the TUF ID, so a single formula fixes the whole Resource column.
With the TUF ID in column `M` (A2Z tab) or `K` (SDE and Blind 75 tabs):

```
=HYPERLINK("https://udhayakumar-gj.github.io/dsa-java-articles/p/"&M2&".html","Article")
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
jekyll serve --baseurl /dsa-java-articles   # then open http://127.0.0.1:4000/dsa-java-articles/
```

## Publishing

GitHub Pages serves the `main` branch from the repository root (Settings → Pages → Deploy from a branch → `main` / `/`).
