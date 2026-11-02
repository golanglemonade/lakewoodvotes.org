# Lakewood Votes

A sourced, nonpartisan guide to everything on the **November 3, 2026** ballot for voters in the City of Lakewood, Jefferson County, Colorado: federal and statewide offices, the state legislature districts that cover Lakewood, Jefferson County offices, judges up for retention, all 14 statewide measures, and the local measures (City of Lakewood 2G–2J, Jeffco Schools 5A/5B, Front Range Passenger Rail 7A, West Metro Fire 7C).

Adapted from [Boulder Votes](https://github.com/Unforced-Dev/bouldervotes.org) and keeps its editorial line: large type for older readers, one column, no JavaScript needed, **every fact links to its source**, no endorsements, no scores.

## Run it

With [Task](https://taskfile.dev) (`brew install go-task`): `task local` (build for local testing and open it), `task check` (tests, then the live build — run before committing), `task serve`, `task` to list everything. Or by hand:

```bash
python3 build.py          # writes docs/ (GitHub Pages)
python3 -m unittest       # every fact has a source, every source resolves, no broken links
open docs/index.html
```

Python 3 stdlib only. `LV_TODAY=YYYY-MM-DD` pins the "today" marker on the key-dates timeline (default: the build date, so rebuild daily during the election).

## Where things live

- `data/2026/*.json` — the record. One file per section; each has `sources`, `contests`, `retention`, `measures`, `facts`, `open_questions`. The builder never adds facts.
- `data/people/*.json` — candidate research for the local races: bios, endorsements (with who-says-so labels), questionnaire answers, campaign money.
- `schema.sql` + `seed.py` — every build rebuilds `data/lakewoodvotes.db` (SQLite, not committed) from all the JSON, joining people across elections. `build_people.py` renders `people.html` and `people/<id>.html` from it.
- `build.py` — renders the pages, `llms.txt`, `llms-full.txt`, `api/ballot.json`, sitemap and `CNAME`.
- `static/css/site.css` — shared with Boulder Votes; `static/css/lakewood.css` holds the few additions.
- `REVIEW.md` — open questions from research to check before launch.

## Publish

GitHub Pages from `/docs` on `main`, custom domain `lakewoodvotes.org` (the `CNAME` file is generated). See OPERATING.md for DNS.
