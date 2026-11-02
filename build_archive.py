"""Past-election archive pages for Lakewood Votes (data/archive/*.json -> docs/<slug>.html).

Same rules as the 2026 guide: certified numbers copied from the cited source, a label when a count is
not certified, nothing estimated. Each archive file has its own source ids, so citations are resolved
per file (ids may repeat across years with different URLs).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parent / "data" / "archive"

LEVEL_LABELS = (
    ("federal", "Federal offices"),
    ("state", "Colorado statewide offices"),
    ("legislature", "Colorado legislature"),
    ("county", "Jefferson County offices"),
    ("city", "City of Lakewood"),
    ("district", "Regional districts"),
    ("school", "Jeffco Public Schools board"),
)
STATUS_NOTE = {
    "certified": "",
    "official final": "Official final count.",
    "unofficial final": "Unofficial final count; not yet certified when we checked.",
    "partial": "Preliminary count from a news report; the certified count was not on file.",
}



def short_pub(p: str) -> str:
    return re.split(r" \(|, ", p)[0].strip()


class Election:
    def __init__(self, path: Path) -> None:
        self.raw = json.loads(path.read_text())
        self.e = self.raw["election"]
        self.sources = {s["id"]: s for s in self.raw["sources"]}
        self.contests = self.raw.get("contests", [])
        self.measures = self.raw.get("measures", [])
        self.facts = self.raw.get("facts", [])
        self.used: set[str] = set()

    @property
    def slug(self) -> str:
        # 2023-11-lakewood -> 2023 ; 2026-04-lakewood-special -> 2026-april
        y, m = self.e["date"][:4], self.e["date"][5:7]
        return y if m == "11" else f"{y}-{_MONTHS[int(m)].lower()}"

    @property
    def label(self) -> str:
        y, m = self.e["date"][:4], int(self.e["date"][5:7])
        return y if m == 11 else f"{_MONTHS[m]} {y}"


_MONTHS = ["", "January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]


def load_all() -> list[Election]:
    els = [Election(p) for p in sorted(ARCHIVE.glob("*.json"))]
    return sorted(els, key=lambda x: x.e["date"], reverse=True)


def _cite(el: Election, ids, esc) -> str:
    seen, by_pub = set(), {}
    for sid in ids or []:
        s = el.sources[sid]
        el.used.add(sid)
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        by_pub.setdefault(short_pub(s["publisher"]), []).append(s)
    parts = []
    for pub, ss in by_pub.items():
        if len(ss) == 1:
            parts.append(f"<a href='{esc(ss[0]['url'])}' title='{esc(ss[0]['title'])}'>{esc(pub)}</a>")
        else:
            nums = ", ".join(f"<a href='{esc(x['url'])}' title='{esc(x['title'])}'>{i}</a>" for i, x in enumerate(ss, 1))
            parts.append(f"{esc(pub)} ({nums})")
    if not parts:
        return ""
    return f"<span class='src'>Source{'s' if len(seen) > 1 else ''}: {'; '.join(parts)}</span>"


def _n(v) -> str:
    return "—" if v is None else f"{v:,}"


def _pct(v) -> str:
    return "—" if v is None else f"{v:.1f}%"


def _status(st: str | None, esc) -> str:
    note = STATUS_NOTE.get(st or "certified", f"Status: {st}.")
    return f"<p class='note'>{esc(note)}</p>" if note else ""


def contest_html(el: Election, c: dict, esc) -> str:
    rows = []
    for x in sorted(c["candidates"], key=lambda x: -(x.get("votes") or 0)):
        won = " class='won'" if x.get("won") else ""
        badge = " <span class='badge elected'>Won</span>" if x.get("won") else ""
        inc = " <span class='meta'>(incumbent)</span>" if x.get("incumbent") else ""
        party = esc(x.get("party") or ("Nonpartisan" if c.get("nonpartisan") else "—"))
        rows.append(f"<tr{won}><td>{esc(x['name'])}{inc}{badge}</td><td>{party}</td>"
                    f"<td class='num'>{_n(x.get('votes'))}</td><td class='num'>{_pct(x.get('pct'))}</td></tr>")
    title = esc(c["office"]) + (f" — {esc(c['district'])}" if c.get("district") else "")
    notes = f"<p class='note'>{esc(c['notes'])}</p>" if c.get("notes") else ""
    return (f"<article class='card archive-race'><h3>{title}</h3><p class='meta'>Who voted: {esc(c.get('who_voted') or '—')}</p>"
            f"<div class='table-scroll'><table><thead><tr><th>Candidate</th><th>Party</th><th class='num'>Votes</th>"
            f"<th class='num'>Share</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
            f"{notes}{_status(c.get('results_status'), esc)}<p class='meta'>{_cite(el, c.get('sources'), esc)}</p></article>")


def _is_judge(m: dict) -> bool:
    return m["number"].lower().startswith("judicial retention")


def measures_table(el: Election, ms: list[dict], esc, judges: bool = False) -> str:
    rows = []
    for m in ms:
        if judges:
            outcome = "Kept" if m.get("passed") else "Removed"
            first = esc(m["short_title"])
        else:
            outcome = "Passed" if m.get("passed") else "Failed"
            first = (f"<strong>{esc(m['number'])}</strong> {esc(m['short_title'])}"
                     f"<details class='fold'><summary>What it did</summary><p>{esc(m['summary'])}</p></details>")
        status = STATUS_NOTE.get(m.get("results_status") or "certified", "")
        status = f"<br><span class='meta'>{esc(status)}</span>" if status else ""
        rows.append(f"<tr{' class=won' if m.get('passed') else ''}><td>{first}</td>"
                    f"<td class='num'>{_n(m.get('yes_votes'))}</td><td class='num'>{_n(m.get('no_votes'))}</td>"
                    f"<td class='num'>{_pct(m.get('yes_pct'))}</td><td><strong>{outcome}</strong>{status}</td>"
                    f"<td>{_cite(el, m.get('sources'), esc)}</td></tr>")
    head = "Judge" if judges else "Measure"
    return (f"<div class='table-scroll'><table class='archive-measures-table'><thead><tr><th>{head}</th>"
            f"<th class='num'>Yes</th><th class='num'>No</th><th class='num'>Yes share</th><th>Result</th><th>Sources</th>"
            f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def election_page(el: Election, all_els: list[Election], esc, linkify, plural) -> str:
    e = el.e
    chips = "".join(f"<a href='{x.slug}.html'{' aria-current=page' if x is el else ''}>{esc(x.label)}</a>" for x in all_els)
    parts = [f"<nav class='yearbar' aria-label='Past elections'><div class='wrap'><span>Past elections:</span>{chips}"
             f"<a href='index.html'>2026 (this election)</a></div></nav>",
             f"<p class='crumb'><a href='past.html'>Past elections</a> › {esc(el.label)}</p>",
             f"<p class='kicker'>Past election · results</p><h1>{esc(e['name'])}</h1>",
             f"<p class='lede'>{esc(e['summary'])}</p>"]
    if e.get("turnout"):
        parts.append(f"<p><strong>Turnout:</strong> {esc(e['turnout'])} {_cite(el, e.get('sources'), esc)}</p>")
    parts.append("<p class='note'>Vote counts are copied from the cited official reports. Where Lakewood-only numbers "
                 "weren't published, the count is for all of Jefferson County, and the race notes say so.</p>")
    jump_at = len(parts)
    jump = []
    for lv, label in LEVEL_LABELS:
        cs = [c for c in el.contests if c["level"] == lv]
        if not cs:
            continue
        jump.append(f"<a href='#{lv}'>{esc(label)}</a>")
        parts.append(f"<div class='section-head'><h2 id='{lv}'>{esc(label)}</h2><span class='count'>{plural(len(cs), 'race')}</span></div>")
        parts.append(f"<div class='archive-grid'>{''.join(contest_html(el, c, esc) for c in cs)}</div>")
    groups: dict[str, list[dict]] = {}
    for m in el.measures:
        if not _is_judge(m):
            groups.setdefault(m["jurisdiction"], []).append(m)
    for jur, ms in groups.items():
        anchor = "m-" + "".join(ch if ch.isalnum() else "-" for ch in jur.lower()).strip("-")
        jump.append(f"<a href='#{anchor}'>{esc(jur)} measures</a>")
        parts.append(f"<div class='section-head'><h2 id='{anchor}'>{esc(jur)} measures</h2><span class='count'>{plural(len(ms), 'measure')}</span></div>")
        parts.append(measures_table(el, ms, esc))
    judges = [m for m in el.measures if _is_judge(m)]
    if judges:
        jump.append("<a href='#judges'>Judges</a>")
        parts.append(f"<div class='section-head'><h2 id='judges'>Judges up for retention</h2><span class='count'>{plural(len(judges), 'judge')}</span></div>")
        by: dict[str, list[dict]] = {}
        for m in judges:
            by.setdefault(m["jurisdiction"], []).append(m)
        for court, ms in by.items():
            parts.append(f"<h3>{esc(court)}</h3>{measures_table(el, ms, esc, judges=True)}")
    if el.facts:
        lis = "".join(f"<li>{linkify(f['text'])} {_cite(el, f.get('sources'), esc)}</li>" for f in el.facts)
        parts.append(f"<section class='panel'><h2 id='context'>Good to know</h2><ul class='facts'>{lis}</ul></section>")
        jump.append("<a href='#context'>Good to know</a>")
    parts.insert(jump_at, f"<p class='jump'>{''.join(jump)}</p>")
    srcs = "".join(f"<li><a href='{esc(s['url'])}'>{esc(s['title'])}</a> <span class='meta'>— {esc(s['publisher'])}</span></li>"
                   for sid, s in el.sources.items() if sid in el.used)
    parts.append(f"<section class='panel'><h2>Sources</h2><ul class='sources'>{srcs}</ul></section>")
    return "\n".join(parts)


def index_page(els: list[Election], esc) -> str:
    cards = []
    for el in els:
        e = el.e
        n_c, n_m = len(el.contests), len([m for m in el.measures if not _is_judge(m)])
        what = ", ".join(x for x in (f"{n_c} races" if n_c else "", f"{n_m} measures" if n_m else "") if x)
        cards.append(f"<a class='race' href='{el.slug}.html'><span class='kicker'>{esc(el.label)}</span>"
                     f"<h3>{esc(e['name'])}</h3><p>{esc(e['summary'])}</p><span class='go'>Results: {esc(what)}</span></a>")
    return ("<h1>Past elections</h1><p class='lede'>Who ran, who won, and how the measures did in recent elections on Lakewood "
            "ballots. Every number links to the official count it came from.</p>"
            f"<div class='races'>{''.join(cards)}</div>")


def llm_text(els: list[Election]) -> str:
    out = ["## Past elections (results)", ""]
    for el in els:
        out += [f"### {el.e['name']}", el.e["summary"]]
        for c in el.contests:
            win = ", ".join(x["name"] for x in c["candidates"] if x.get("won")) or "—"
            out.append(f"- {c['office']}{' (' + c['district'] + ')' if c.get('district') else ''}: won by {win}. "
                       + "; ".join(f"{x['name']} {_n(x.get('votes'))}" for x in c["candidates"]))
        for m in el.measures:
            out.append(f"- {m['number']} ({m['jurisdiction']}): {m['short_title']} — "
                       f"{'passed' if m.get('passed') else 'failed'}, yes {_n(m.get('yes_votes'))}, no {_n(m.get('no_votes'))}")
        out += ["Sources: " + ", ".join(sorted({s['url'] for s in el.sources.values()})), ""]
    return "\n".join(out) + "\n"
