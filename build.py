"""Render Lakewood Votes from the sourced JSON in data/2026/ into docs/ (GitHub Pages).

Python 3 stdlib only. The JSON files are the record; this script never adds facts.
Editorial rules (same as Boulder Votes): every fact links to its source, no endorsements,
no scores, a dash or "not on file" when we don't have it.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import shutil

import build_archive
import build_people
import seed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "2026"
OUT = Path(os.environ["LV_OUT"]) if os.environ.get("LV_OUT") else ROOT / "docs"  # tests build elsewhere

SITE_NAME = "Lakewood Votes"
SITE_URL = "https://lakewoodvotes.org/"
# Where the AI prompt on the home page points. Set LV_SITE_URL to test before the site is live, e.g.
#   LV_SITE_URL=file:///Users/you/lakewoodvotes/docs/ python3 build.py
# A file:// address can't be read by an online AI, so the prompt then asks you to attach llms-full.txt instead.
PROMPT_URL = os.environ.get("LV_SITE_URL", SITE_URL).rstrip("/") + "/"
DOMAIN = "lakewoodvotes.org"
# One place to change the repository address.
REPO_URL = os.environ.get("LV_REPO_URL", "https://github.com/golanglemonade/lakewoodvotes.org")
ELECTION_DAY = dt.date(2026, 11, 3)
ELECTION_LABEL = "Tuesday, November 3, 2026"
TAGLINE = "A nonpartisan guide to everything on a Lakewood, Colorado ballot. Every fact links to its source."
SAMPLE_BALLOT_URL = "https://www.jeffco.us/DocumentCenter/View/59222"
FIND_BALLOT_URL = "https://www.govotecolorado.gov/"

FILES = ("federal_statewide", "state_measures", "legislature", "county_judicial", "local_and_voting")

# Office groups, in ballot order.
LEVELS = (
    ("federal", "Federal offices", "Everyone in Lakewood votes on these."),
    ("state", "Colorado statewide offices", "Everyone in Lakewood votes on these."),
    ("legislature", "Colorado legislature", "Lakewood is split among several districts. You vote in one House district and one Senate district."),
    ("county", "Jefferson County offices", "Everyone in Lakewood votes on these."),
)

# Key dates. Each row cites a source id from the data files.
KEY_DATES = (
    ("2026-10-05", "Ballots mailed; 24-hour drop boxes open", "src-jeffco-elections"),
    ("2026-10-19", "Voter Service and Polling Centers open for in-person voting", "src-jeffco-elections"),
    ("2026-10-26", "Last day to register and still get a ballot in the mail; last recommended day to mail your ballot back", "src-jeffco-elections"),
    ("2026-11-03", "Election Day: ballots must be received by 7 p.m. You can still register and vote in person that day.", "src-jeffco-elections"),
)

PRIMARY_NAV = (
    ("home", "index.html", "Your ballot"),
    ("ballot", "my-ballot.html", "Sample ballot"),
    ("offices", "offices.html", "Offices"),
    ("measures", "measures.html", "Measures"),
    ("judges", "judges.html", "Judges"),
    ("vote", "vote.html", "How to vote"),
    ("people", "people.html", "People"),
    ("past", "past.html", "Past elections"),
)

LOGO_SVG = (
    '<svg viewBox="0 0 40 40" role="img" aria-label="Lakewood Votes logo" focusable="false">'
    '<rect width="40" height="40" rx="9" fill="currentColor"/>'
    # Green Mountain's long ridge over a lake line, over a ballot line.
    '<path d="M5 25 C10 20 14 13 20 12 C26 11 30 17 35 25 Z" fill="#fff"/>'
    '<path d="M7 27.5 H33" stroke="#fff" stroke-width="1.6" opacity=".6"/>'
    '<rect x="7" y="31" width="26" height="2.6" rx="1.3" fill="#fff"/></svg>'
)


# ---------- helpers ----------

def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


URL_RE = re.compile(r"https?://[^\s)<>\"']+")


def linkify(text: str) -> str:
    """Escape plain text and turn bare URLs into links (trailing period stays text)."""
    out, last = [], 0
    for m in URL_RE.finditer(text or ""):
        url = m.group(0).rstrip(".,;:")
        out.append(esc(text[last:m.start()]))
        out.append(f"<a href='{esc(url)}'>{esc(url)}</a>")
        last = m.start() + len(url)
    out.append(esc((text or "")[last:]))
    return "".join(out)


def short_pub(p: str) -> str:
    """Publisher name for inline citations: drop a trailing ', Division' or ' (detail)'."""
    return re.split(r" \(|, ", p)[0].strip()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def nice_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def short_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}"


def plural(n: int, word: str, many: str | None = None) -> str:
    return f"{n} {word if n == 1 else (many or word + 's')}"


PARTY_SHORT = {"Democratic": "D", "Republican": "R", "Libertarian": "L", "Unaffiliated": "U"}


def party_label(p: str | None) -> str:
    if not p:
        return "No party listed"
    return p if p.endswith("Party") or p == "Unaffiliated" else f"{p} Party"


def measure_code(number: str) -> str:
    """'Amendment 81' -> '81', 'Proposition NN' -> 'NN', 'Ballot Issue 2G' -> '2G'."""
    return number.split()[-1]


# ---------- load ----------

class Data:
    def __init__(self) -> None:
        self.files = {name: json.loads((DATA / f"{name}.json").read_text()) for name in FILES}
        self.sources: dict[str, dict] = {}
        for name, d in self.files.items():
            for s in d["sources"]:
                prev = self.sources.get(s["id"])
                if prev and prev["url"] != s["url"]:
                    raise SystemExit(f"source id {s['id']} has two URLs ({name})")
                self.sources[s["id"]] = s
        self.contests = [c for n in FILES for c in self.files[n].get("contests", [])]
        self.retention = [r for n in FILES for r in self.files[n].get("retention", [])]
        self.measures = [m for n in FILES for m in self.files[n].get("measures", [])]
        self.cited: set[str] = set()

    def facts(self, name: str) -> list[dict]:
        return self.files[name].get("facts", [])


D: Data


def cite(ids: list[str] | None, label: str = "Source") -> str:
    """Inline citation: one link per distinct URL, grouped by publisher ("Jeffco Clerk (1, 2)")."""
    by_pub: dict[str, list[str]] = {}
    seen: set[str] = set()
    for sid in ids or []:
        s = D.sources[sid]
        D.cited.add(sid)
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        by_pub.setdefault(short_pub(s["publisher"]), []).append(s)
    if not by_pub:
        return ""
    parts = []
    for pub, ss in by_pub.items():
        if len(ss) == 1:
            parts.append(f"<a href='{esc(ss[0]['url'])}' title='{esc(ss[0]['title'])}'>{esc(pub)}</a>")
        else:
            nums = ", ".join(f"<a href='{esc(x['url'])}' title='{esc(x['title'])}'>{i}</a>" for i, x in enumerate(ss, 1))
            parts.append(f"{esc(pub)} ({nums})")
    return f"<span class='src'>{label}{'s' if len(seen) > 1 else ''}: {'; '.join(parts)}</span>"


def source_list(ids: list[str]) -> str:
    seen, items = set(), []
    for sid in ids:
        s = D.sources[sid]
        D.cited.add(sid)
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        items.append(f"<li><a href='{esc(s['url'])}'>{esc(s['title'])}</a> <span class='meta'>— {esc(s['publisher'])}, "
                     f"retrieved {nice_date(s['retrieved_on'])}</span></li>")
    return f"<ul class='sources'>{''.join(items)}</ul>"


def all_ids(*objs) -> list[str]:
    """Every source id cited anywhere inside the given objects, in first-seen order."""
    out: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "sources" and isinstance(v, list) and all(isinstance(x, str) for x in v):
                    out.extend(x for x in v if x not in out)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    for o in objs:
        walk(o)
    return out


# ---------- chrome ----------

def page(title: str, body: str, *, prefix: str = "", current: str | None = None, desc: str | None = None) -> str:
    nav = "".join(
        '<li><a href="{}{}"{}>{}</a></li>'.format(prefix, href, ' aria-current="page"' if key == current else "", label)
        for key, href, label in PRIMARY_NAV)
    description = desc or ("Nonpartisan guide to the November 3, 2026 election for Lakewood, Colorado voters: "
                           "federal, state, legislature, Jefferson County, judges and every ballot measure, with a source for every fact.")
    full_title = SITE_NAME if title == SITE_NAME else f"{title} — {SITE_NAME}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="preload" href="{prefix}fonts/source-serif-4.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{prefix}fonts/source-sans-3.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{prefix}css/site.css">
<link rel="stylesheet" href="{prefix}css/lakewood.css">
<script defer src="{prefix}js/lookup.js"></script>
<script defer src="{prefix}js/ballot.js"></script>
<link rel="alternate" type="text/markdown" href="/llms-full.txt" title="Full guide for AI assistants">
<meta name="theme-color" content="#017cc4">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
</head>
<body>
<a class="skip" href="#content">Skip to main content</a>
<header class="site">
  <div class="bar">
    <a class="brand" href="{prefix}index.html">{LOGO_SVG}<span><span class="brand-name">{SITE_NAME}</span><span class="brand-sub">Lakewood, Colorado · November 3, 2026</span></span></a>
    <nav class="primary" aria-label="Main"><ul>{nav}</ul></nav>
  </div>
</header>
<main id="content">
{body}
</main>
<footer class="site">
  <div class="footer-inner">
    <div>
      <h2>{SITE_NAME}</h2>
      <p>{esc(TAGLINE)}</p>
      <p>We don't endorse candidates or measures.</p>
      <p class="ai-foot">Open data: <a href="{prefix}llms-full.txt">the whole guide as one text file</a> · <a href="{prefix}api/ballot.json">JSON</a> · <a href="{prefix}llms.txt">llms.txt</a></p>
      <p><a href="{REPO_URL}">Source code on GitHub</a> · <a href="{REPO_URL}/issues">Spot a mistake? Tell us</a></p>
      <p class="credit">Adapted from <a href="https://bouldervotes.org/">Boulder Votes</a> (<a href="https://github.com/Unforced-Dev/bouldervotes.org">source on GitHub</a>), with thanks.</p>
    </div>
    <div>
      <h2>2026 ballot</h2>
      <ul>
        <li><a href="{prefix}offices.html">Offices and candidates</a></li>
        <li><a href="{prefix}measures.html">Ballot measures</a></li>
        <li><a href="{prefix}judges.html">Judges</a></li>
        <li><a href="{prefix}my-ballot.html">Printable sample ballot</a></li>
        <li><a href="{prefix}vote.html">How and when to vote</a></li>
      </ul>
    </div>
    <div>
      <h2>About</h2>
      <ul>
        <li><a href="{prefix}about.html">About this guide</a></li>
        <li><a href="{prefix}past.html">Past elections</a></li>
        <li><a href="{prefix}sources.html">Sources</a></li>
        <li><a href="{SAMPLE_BALLOT_URL}">Jefferson County sample ballot</a></li>
      </ul>
    </div>
  </div>
</footer>
</body>
</html>
"""


# ---------- pieces ----------

def timeline(today: dt.date) -> str:
    items, nxt = [], None
    rows = [(dt.date.fromisoformat(d), t, s) for d, t, s in KEY_DATES]
    placed = False
    for d, t, s in rows:
        if not placed and d > today:
            items.append(f"<li class='today' aria-current='date'><time class='d' datetime='{today.isoformat()}'>"
                         f"{short_date(today.isoformat())}</time><span class='t'>Today</span></li>")
            placed = True
        if d > today and nxt is None:
            nxt = (d, t)
        cls = " class='done'" if d < today else (" class='today' aria-current='date'" if d == today else "")
        items.append(f"<li{cls}><time class='d' datetime='{d.isoformat()}'>{short_date(d.isoformat())}</time>"
                     f"<span class='t'>{esc(t)}</span></li>")
    count = ""
    if nxt:
        days = (nxt[0] - today).days
        count = f"<p class='countdown'>Next: {esc(nxt[1].split(';')[0].split(':')[0])} in {plural(days, 'day')}.</p>"
    src = cite([s for _, _, s in KEY_DATES])
    return (f"<section class='timeline' aria-labelledby='dates'><div class='timeline-head'><h2 id='dates'>Key dates</h2>"
            f"<span class='asof'>As of {nice_date(today.isoformat())}</span></div>{count}<ol>{''.join(items)}</ol>"
            f"<p class='note'>Your ballot must be <em>received</em> by 7 p.m. on Election Day. Postmarks don't count. {src}</p></section>")


def cand_line(c: dict) -> str:
    inc = " <span class='badge'>Incumbent</span>" if c.get("incumbent") else ""
    wi = " <span class='badge'>Write-in</span>" if c.get("write_in") else ""
    site = f" · <a href='{esc(c['website'])}'>Campaign website</a>" if c.get("website") else ""
    return (f"<li><strong>{esc(c['name'])}</strong>{inc}{wi}<br><span class='meta'>{esc(party_label(c.get('party')))}{site}</span></li>")


def ballot_sorted(cands: list[dict]) -> list[dict]:
    return sorted(cands, key=lambda c: (c.get("ballot_order") is None, c.get("ballot_order") or 0, c["name"]))


def contest_card(c: dict, prefix: str = "") -> str:
    cands = ballot_sorted(c["candidates"])
    names = "".join(f"<li>{esc(x['name'])} <span class='party'>({esc(PARTY_SHORT.get(x.get('party') or '', x.get('party') or '—'))}"
                    f"{', incumbent' if x.get('incumbent') else ''})</span></li>" for x in cands)
    sub = f"{esc(c['district'])} · " if c.get("district") else ""
    vote_for = "Vote for one" if c.get("seats", 1) == 1 else f"Vote for up to {c['seats']}"
    return (f"<a class='race' data-race='{esc(c['id'])}' href='{prefix}races/{esc(c['id'])}.html'><span class='kicker'>{sub}{esc(vote_for)}</span>"
            f"<h3>{esc(c['office'])}</h3><ol class='names'>{names}</ol>"
            f"<span class='go'>{plural(len(cands), 'candidate')} · details and sources</span></a>")


def measure_row(m: dict, prefix: str = "") -> str:
    return (f"<li><a href='{prefix}measures/{esc(m['id'])}.html'><span class='code'>{esc(measure_code(m['number']))}</span>"
            f"<span>{esc(m['short_title'])}</span></a></li>")


def measure_groups() -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for m in D.measures:
        groups.setdefault(m["jurisdiction"], []).append(m)
    return list(groups.items())


def facts_block(name: str, heading: str = "Good to know", keys: tuple[str, ...] | None = None) -> str:
    facts = [f for f in D.facts(name) if keys is None or f["key"] in keys]
    if not facts:
        return ""
    lis = "".join(f"<li>{linkify(f['text'])} {cite(f['sources'])}</li>" for f in facts)
    return f"<section class='panel'><h2>{esc(heading)}</h2><ul class='facts'>{lis}</ul></section>"


def lookup_form(prefix: str = "") -> str:
    """Address -> House/Senate district. Hidden until lookup.js runs, so no-JS readers just see the links."""
    races = {c["id"]: ", ".join(f"{x['name']} ({PARTY_SHORT.get(x.get('party') or '', x.get('party'))})"
                                for x in ballot_sorted(c["candidates"]))
             for c in D.contests if c["level"] == "legislature"}
    return (f"<form id='lookup-form' class='lookup' hidden data-prefix='{prefix}' data-races='{esc(json.dumps(races))}'>"
            "<label for='lookup-addr'>Your street address</label>"
            "<div class='lookup-row'><input id='lookup-addr' name='address' type='text' autocomplete='street-address' "
            "placeholder='e.g. 480 S Allison Pkwy, Lakewood, CO 80226' required>"
            "<button type='submit' class='btn'>Find my districts</button></div>"
            "<p class='note'>Your address is sent only to the "
            "<a href='https://geocoding.geo.census.gov/geocoder/'>U.S. Census Bureau's address lookup</a> "
            "to find your districts. We don't keep it.</p></form>"
            "<div id='lookup-result' class='lookup-result' tabindex='-1' aria-live='polite'></div>")


# ---------- pages ----------

def build_home(today: dt.date) -> str:
    offices_by_level = {lv: [c for c in D.contests if c["level"] == lv] for lv, _, _ in LEVELS}
    n_offices = len(D.contests)
    n_state_m = sum(1 for m in D.measures if m["jurisdiction"] == "State of Colorado")
    n_local_m = len(D.measures) - n_state_m
    races = []
    for lv, label, _ in LEVELS:
        cs = offices_by_level[lv]
        if not cs:
            continue
        lis = "".join(f"<li>{esc(c['district'] if lv == 'legislature' else c['office'] + (' — ' + c['district'] if c.get('district') else ''))}</li>" for c in cs)
        races.append(f"<a class='race' href='offices.html#{lv}'><span class='kicker'>Offices</span><h3>{esc(label)}</h3>"
                     f"<ul class='names'>{lis}</ul><span class='go'>See the candidates</span></a>")
    for jur, ms in measure_groups():
        codes = "".join(f"<li><span class='code'>{esc(measure_code(m['number']))}</span><span>{esc(m['short_title'])}</span></li>" for m in ms)
        races.append(f"<a class='race' href='measures.html#{slug(jur)}'><span class='kicker'>Measures</span>"
                     f"<h3>{esc(jur)}</h3><ul class='codes'>{codes}</ul><span class='go'>What Yes and No mean</span></a>")
    races.append(f"<a class='race' href='judges.html'><span class='kicker'>Judges</span><h3>Keep these judges?</h3>"
                 f"<p>{plural(len(D.retention), 'judge')} on the ballot. You vote Yes or No on keeping each one.</p>"
                 f"<span class='go'>See the judges and their reviews</span></a>")
    ask = "Help me understand my ballot for the November 3, 2026 election in Lakewood, Colorado. "
    then = "Ask me what matters to me, then walk me through each race and measure, with links to the sources."
    if PROMPT_URL.startswith("file://"):
        prompt = ask + "I've attached llms-full.txt, the full Lakewood Votes guide. Use only that file and the sources it links. " + then
        attach = (f"<p class='note tiny'>Testing locally: attach <a href='{PROMPT_URL}llms-full.txt' download>llms-full.txt</a> "
                  f"(in your <code>docs</code> folder) to the chat along with this prompt.</p>")
    else:
        prompt = ask + f"Start by reading {PROMPT_URL}llms.txt and follow its instructions. " + then
        attach = ""
    return f"""<div class='hero'>
<p class='eyebrow'>Lakewood, Colorado · Election Day {ELECTION_LABEL}</p>
<h1>Everything on your Lakewood ballot, with sources</h1>
<p class='intro'>Who is running, what each measure would do, and which judges are up for a vote. We don't endorse anyone. Every name, number and date links to its source.</p>
</div>
<section class='ask-box ask-combo' id='my-districts' aria-labelledby='ask-h'>
<h2 id='ask-h' class='visually-hidden'>Your districts and an AI prompt</h2>
<div class='ask-step'>
<h3><span class='step-num'>1</span> Find your state House and Senate races</h3>
<p>Most of the ballot is the same for everyone in Lakewood. Your state House and Senate races depend on where you live.</p>
{lookup_form()}
<p class='note'>Or look up your exact ballot at <a href='{FIND_BALLOT_URL}'>GoVoteColorado.gov</a>, or read the <a href='{SAMPLE_BALLOT_URL}'>Jefferson County sample ballot</a>.</p>
</div>
<div class='ask-step'>
<div class='ask-head'><h3><span class='step-num'>2</span> Prefer to ask an AI? Copy this into ChatGPT, Claude, or any assistant:</h3><button type='button' class='btn secondary copy' id='ai-copy' hidden>Copy</button></div>
<p class='prompt-box' id='ai-prompt'>{esc(prompt)}</p><p class='note' id='ai-prompt-note' hidden>Your districts from step 1 are included, so the assistant won't need to ask. Your address is not.</p>{attach}
<p class='note ask-foot'>AI assistants can get things wrong. Every claim on this site links to its source, so check the links.</p>
</div>
</section>
{timeline(today)}
<p class='note'>There is no Lakewood mayor or city council race this year. Lakewood elects its mayor and council in odd-numbered years; the next is November 2027. {cite(['src-lkw-elections'])}</p>
<h2 class='visually-hidden'>On your ballot</h2>
<p class='lede'>{plural(n_offices, 'office')}, {plural(len(D.retention), 'judge')}, {n_state_m} statewide measures and {n_local_m} local measures.</p>
<div class='races'>
{''.join(races)}
</div>
<p class='about-line'>{SITE_NAME} is an independent, nonpartisan guide for voters in the City of Lakewood, Jefferson County, Colorado. <a href='about.html'>How we put it together</a>.</p>
"""


def build_offices() -> str:
    parts = ["<h1>Offices and candidates</h1>",
             "<p class='lede'>Candidates are listed in the order they appear on the ballot. Open a race for what the job is, who votes on it, and the sources.</p>"]
    jump = "".join(f"<a href='#{lv}'>{esc(label)}</a>" for lv, label, _ in LEVELS)
    parts.append(f"<p class='jump'>{jump}</p>")
    for lv, label, note in LEVELS:
        cs = [c for c in D.contests if c["level"] == lv]
        if not cs:
            continue
        parts.append(f"<div class='section-head'><h2 id='{lv}'>{esc(label)}</h2><span class='count'>{plural(len(cs), 'race')}</span></div>")
        parts.append(f"<p>{esc(note)}</p>")
        if lv == "legislature":
            parts.append(f"<section class='panel callout'><h2>Which districts are yours?</h2>{lookup_form()}</section>")
            parts.append(facts_block("legislature", "Which districts cover Lakewood",
                                     ("lakewood-house-districts", "lakewood-senate-districts")))
        if lv == "county":
            parts.append(facts_block("county_judicial", "About county races",
                                     ("commissioners-elected-at-large", "kerr-possible-vacancy")))
        parts.append(f"<div class='races'>{''.join(contest_card(c) for c in cs)}</div>")
    parts.append("<p class='note'>Not on the 2026 ballot: Lakewood mayor and city council (next in 2027) and the 1st Judicial District attorney.</p>")
    return "\n".join(parts)


def build_race(c: dict) -> str:
    cands = ballot_sorted(c["candidates"])
    rows = []
    for x in cands:
        pos = f"<p class='ballot-pos'>Ballot position {x['ballot_order']}</p>" if x.get("ballot_order") else ""
        inc = " <span class='badge'>Incumbent</span>" if x.get("incumbent") else ""
        site = f"<p class='meta'><a href='{esc(x['website'])}'>Campaign website</a></p>" if x.get("website") else ""
        pids = G.person_for(c["id"], x["name"])
        if len(pids) == 1:
            name_html = f"<a href='../people/{pids[0]}.html'>{esc(x['name'])}</a>"
        else:  # a ticket: link each person
            name_html = " / ".join(f"<a href='../people/{pid}.html'>{esc(n)}</a>" for pid, n in zip(pids, x["name"].split(" / ")))
        extra = ""
        if len(pids) == 1:
            sm = G.summary(pids[0], c["id"])
            if sm["bio"]:
                extra += f"<p class='bio'>{esc(sm['bio'])}</p>"
                if not site and G.q("SELECT website FROM people WHERE id = ?", pids[0])[0]["website"]:
                    site = f"<p class='meta'><a href='{esc(G.q('SELECT website FROM people WHERE id = ?', pids[0])[0]['website'])}'>Campaign website</a></p>"
            facts = []
            if sm["endorsements"]:
                facts.append(f"<a href='../people/{pids[0]}.html#endorsements'>{plural(sm['endorsements'], 'endorsement')}</a>")
            if sm["answers"]:
                facts.append(f"<a href='../people/{pids[0]}.html#answers'>{plural(sm['answers'], 'answer')} in their own words</a>")
            if sm["finance"] and sm["finance"]["raised"] is not None:
                facts.append(f"<a href='../people/{pids[0]}.html#money'>{build_people.money(sm['finance']['raised'])} raised</a>")
            if facts:
                extra += f"<p class='meta'>{' · '.join(facts)}</p>"
        rows.append(f"<article class='card cand-card'>{pos}<h3>{name_html}{inc}</h3>"
                    f"<p class='office'>{esc(party_label(x.get('party')))}</p>{extra}{site}<p class='meta'>{cite(x.get('sources'))}</p></article>")
    level_label = dict((lv, lab) for lv, lab, _ in LEVELS).get(c["level"], c["level"])
    seats = c.get("seats", 1)
    term = f"{c['term_years']}-year term" if c.get("term_years") else ""
    notes = f"<section class='panel'><h2>Worth knowing</h2><p>{linkify(c['notes'])}</p></section>" if c.get("notes") else ""
    return f"""<p class='crumb'><a href='../index.html'>2026 ballot</a> › <a href='../offices.html#{c['level']}'>{esc(level_label)}</a> › {esc(c['office'])}</p>
<p class='kicker'>{esc(c.get('district') or level_label)}</p>
<h1>{esc(c['office'])}</h1>
<dl class='yesno facts-dl'><div><dt>Who votes</dt><dd>{esc(c['who_votes'])}</dd></div><div><dt>How to vote</dt><dd>{'Vote for one' if seats == 1 else f'Vote for up to {seats}'}{(' · ' + term) if term else ''}</dd></div></dl>
<section class='panel'><h2>What the job is</h2><p>{esc(c['what_the_job_is'])}</p><p class='meta'>{cite(c.get('sources'))}</p></section>
<div class='section-head'><h2 id='candidates'>Who's running</h2><span class='count'>{plural(len(cands), 'candidate')} · ballot order</span></div>
<div class='who-list'>{''.join(rows)}</div>
{notes}
<section class='panel'><h2>Sources</h2>{source_list(all_ids(c))}</section>
"""


def build_measures() -> str:
    parts = ["<h1>Ballot measures</h1>",
             "<p class='lede'>Every question Lakewood voters will see, in ballot order. Open one for what a Yes and a No vote mean, what it costs, and who is for and against it.</p>"]
    groups = measure_groups()
    parts.append("<p class='jump'>" + "".join(f"<a href='#{slug(j)}'>{esc(j)}</a>" for j, _ in groups) + "</p>")
    for jur, ms in groups:
        parts.append(f"<div class='section-head'><h2 id='{slug(jur)}'>{esc(jur)}</h2><span class='count'>{plural(len(ms), 'measure')}</span></div>")
        if jur == "State of Colorado":
            parts.append(facts_block("state_measures", "How statewide measures work",
                                     ("amendments-vs-propositions", "how-measures-got-on-ballot")))
        cards = []
        for m in ms:
            cards.append(f"<article class='card measure-card'><h3><a href='measures/{esc(m['id'])}.html'>"
                         f"<span class='code'>{esc(measure_code(m['number']))}</span> {esc(m['short_title'])}</a></h3>"
                         f"<p class='meta'>{esc(m['number'])} · Needs: {esc(m.get('passing_threshold') or '—')}</p>"
                         f"<dl class='yesno compact'><div><dt>Yes means</dt><dd>{esc(m['yes_means'])}</dd></div>"
                         f"<div><dt>No means</dt><dd>{esc(m['no_means'])}</dd></div></dl></article>")
        parts.append(f"<div class='who-list'>{''.join(cards)}</div>")
    return "\n".join(parts)


def side_list(rows: list[dict], who: str) -> str:
    if not rows:
        return f"<p class='empty'>No {who} on file with a source.</p>"
    lis = "".join(f"<li>{esc(r['name'])} {cite(r.get('sources'))}</li>" for r in rows)
    return f"<ul>{lis}</ul>"


def build_measure(m: dict) -> str:
    money = (f"<section class='panel'><h2>Money</h2><p>{linkify(m['money'])}</p></section>" if m.get("money") else "")
    return f"""<p class='crumb'><a href='../index.html'>2026 ballot</a> › <a href='../measures.html#{slug(m['jurisdiction'])}'>{esc(m['jurisdiction'])}</a> › {esc(measure_code(m['number']))}</p>
<p class='kicker'>{esc(m['jurisdiction'])} · {esc(m['number'])}</p>
<h1><span class='code code-lg'>{esc(measure_code(m['number']))}</span> {esc(m['short_title'])}</h1>
<dl class='yesno'><div><dt>A YES vote means</dt><dd>{esc(m['yes_means'])}</dd></div><div><dt>A NO vote means</dt><dd>{esc(m['no_means'])}</dd></div></dl>
<section class='panel'><h2 id='summary'>In plain words</h2><p>{esc(m['summary'])}</p><p class='meta'>{cite(m.get('sources'))}</p></section>
{money}
<section class='panel'><h2>Who votes and what it takes to pass</h2><p><strong>Who votes:</strong> {esc(m['who_votes'])}</p><p><strong>Needs:</strong> {esc(m.get('passing_threshold') or '—')}</p><p><strong>How it got on the ballot:</strong> {esc(m.get('how_it_got_on_ballot') or '—')}</p></section>
<section class='panel'><h2 id='positions'>Who supports it, who opposes it</h2>
<p class='note'>Only groups or people named in a source we can link. This is not a complete list, and it is not our recommendation.</p>
<h3>Supporters</h3>{side_list(m.get('supporters') or [], 'supporters')}
<h3>Opponents</h3>{side_list(m.get('opponents') or [], 'opponents')}</section>
<section class='panel'><h2>Sources</h2>{source_list(all_ids(m))}</section>
"""


def build_ballot() -> str:
    """A practice sample ballot: every contest in ballot order, fill-in bubbles, print-ready.
    Choices live only in the viewer's browser (ballot.js). Never styled to pass as an official ballot."""
    def bubble(name: str, value: str, label: str, sub: str = "") -> str:
        sub_html = f"<span class='b-sub'>{esc(sub)}</span>" if sub else ""
        return (f"<li><label><input type='radio' name='{esc(name)}' value='{esc(value)}'>"
                f"<span class='b-oval' aria-hidden='true'></span><span class='b-name'>{esc(label)}</span>{sub_html}</label></li>")

    blocks = []
    level_names = dict((lv, lab) for lv, lab, _ in LEVELS)
    last = None
    for c in D.contests:
        if c["level"] != last:
            blocks.append(f"<h2 class='b-section'>{esc(level_names.get(c['level'], c['level']))}</h2>")
            last = c["level"]
        opts = "".join(bubble(c["id"], x["name"], x["name"],
                              party_label(x.get("party")) + (" · incumbent" if x.get("incumbent") else ""))
                       for x in ballot_sorted(c["candidates"]))
        dist = f"<p class='b-dist'>{esc(c['district'])}</p>" if c.get("district") else ""
        vote_for = "Vote for one" if c.get("seats", 1) == 1 else f"Vote for up to {c['seats']}"
        blocks.append(f"<fieldset class='b-contest' data-race='{esc(c['id'])}'><legend>{esc(c['office'])}</legend>{dist}"
                      f"<p class='b-rule'>{vote_for}</p><ul class='b-opts'>{opts}</ul>"
                      f"<p class='b-more'><a href='races/{esc(c['id'])}.html'>About this race</a></p></fieldset>")
    blocks.append("<h2 class='b-section'>Judges: should each one stay in office?</h2>")
    for r in D.retention:
        q = f"Shall {r['judge']} of the {r['court']} be retained in office?"
        opts = bubble(r["id"], "yes", "Yes") + bubble(r["id"], "no", "No")
        blocks.append(f"<fieldset class='b-contest b-judge' data-race='{esc(r['id'])}'><legend>{esc(r['court'])}</legend>"
                      f"<p class='b-q'>{esc(q)}</p><ul class='b-opts b-yn'>{opts}</ul>"
                      f"<p class='b-more'>Commission's finding: {esc(r.get('commission_recommendation') or '—')}</p></fieldset>")
    for jur, ms in measure_groups():
        blocks.append(f"<h2 class='b-section'>{esc(jur)} measures</h2>")
        for m in ms:
            opts = bubble(m["id"], "yes", "Yes", m["yes_means"]) + bubble(m["id"], "no", "No", m["no_means"])
            blocks.append(f"<fieldset class='b-contest b-measure' data-race='{esc(m['id'])}'>"
                          f"<legend>{esc(m['number'])}: {esc(m['short_title'])}</legend>"
                          f"<p class='b-rule'>Needs: {esc(m.get('passing_threshold') or '—')}</p><ul class='b-opts b-yn'>{opts}</ul>"
                          f"<p class='b-more'><a href='measures/{esc(m['id'])}.html'>What it would do</a></p></fieldset>")
    return f"""<div class='no-print'>
<h1>Your sample ballot</h1>
<p class='lede'>Everything on a Lakewood ballot, in the order it appears, with bubbles you can fill in. Mark your choices, check them, then print this page and take it with you when you fill out your real ballot.</p>
<section class='panel callout'><h2>Show only your districts</h2>
<p>Lakewood is split among several state House and Senate districts. Enter your address and this page will show only yours.</p>
{lookup_form()}
<p class='note b-alldist'>No address yet: all Lakewood districts are shown below. Look for yours, or use the lookup above.</p>
</section>
<div class='b-tools'><button type='button' class='btn' id='b-print' hidden>Print my ballot</button>
<button type='button' class='btn secondary' id='b-clear' hidden>Clear my choices</button>
<span class='note' id='b-count' aria-live='polite'></span></div>
<p class='note'>Your choices are saved only in this web browser, on this device. Nothing is sent anywhere. Without JavaScript you can still print this page and mark it with a pen.</p>
</div>
<div class='ballot' id='ballot'>
<header class='b-head'>
<p class='b-warn'>PRACTICE SHEET — NOT AN OFFICIAL BALLOT. It cannot be used to vote. Use it to fill out your real ballot.</p>
<h2 class='b-title'>Lakewood, Colorado · General Election · {ELECTION_LABEL}</h2>
<p class='b-meta'>Lakewood Votes · lakewoodvotes.org · <span id='b-districts'>All Lakewood state House and Senate districts shown</span></p>
</header>
{''.join(blocks)}
<p class='b-foot'>Candidates and questions from the Jefferson County sample ballot ({SAMPLE_BALLOT_URL}). Your real ballot shows only the races for your address. Ballots must be received by 7 p.m. on Election Day.</p>
</div>
"""


def build_judges() -> str:
    by_court: dict[str, list[dict]] = {}
    for r in D.retention:
        by_court.setdefault(r["court"], []).append(r)
    parts = ["<h1>Judges on your ballot</h1>",
             "<p class='lede'>Colorado judges are appointed, then voters decide whether to keep them. For each judge you vote Yes (keep) or No (remove). "
             "A state commission reviews each judge and publishes a recommendation; you can read the full review at the links.</p>"]
    keys = ("retention-how-it-works", "retention-evaluations-url")
    fb = facts_block("county_judicial", "How judge retention works", keys) if any(f["key"] in keys for f in D.facts("county_judicial")) else ""
    parts.append(fb)
    for court, rs in by_court.items():
        rows = "".join(f"<tr><td>{esc(r['judge'])}</td><td>{esc(r.get('commission_recommendation') or '—')}</td><td>{cite(r.get('sources'))}</td></tr>" for r in rs)
        parts.append(f"<div class='section-head'><h2 id='{slug(court)}'>{esc(court)}</h2><span class='count'>{plural(len(rs), 'judge')}</span></div>"
                     f"<p class='note'>{esc(rs[0]['who_votes'])}</p>"
                     f"<div class='table-scroll'><table><thead><tr><th>Judge</th><th>Commission's finding</th><th>Sources</th></tr></thead><tbody>{rows}</tbody></table></div>")
    return "\n".join(p for p in parts if p)


def build_vote() -> str:
    CTX = ("april-2026", "no-lakewood", "next-city", "lakewood-tabor", "no-county-rtd", "vacancy-amendment")
    lv = [f for f in D.facts("local_and_voting") if not f["key"].startswith(CTX)]
    lis = "".join(f"<li>{linkify(f['text'])} {cite(f['sources'])}</li>" for f in lv)
    ctx = [f for f in D.facts("local_and_voting") if f["key"].startswith(CTX)]
    ctx_lis = "".join(f"<li>{linkify(f['text'])} {cite(f['sources'])}</li>" for f in ctx)
    return f"""<h1>How and when to vote</h1>
<p class='lede'>Colorado votes by mail. Every registered voter gets a ballot in the mail, and you can return it by mail, at a 24-hour drop box, or vote in person.</p>
{timeline(TODAY)}
<section class='panel'><h2>The details</h2><ul class='facts'>{lis}</ul></section>
<section class='panel'><h2>Lakewood elections: background</h2><ul class='facts'>{ctx_lis}</ul></section>
"""


def build_sources() -> str:
    by_pub: dict[str, list[dict]] = {}
    for sid in sorted(D.cited, key=lambda s: (D.sources[s]["publisher"], D.sources[s]["title"])):
        by_pub.setdefault(D.sources[sid]["publisher"], []).append(D.sources[sid])
    parts = ["<h1>Sources</h1>",
             f"<p class='lede'>Every document this guide cites ({len({D.sources[s]['url'] for s in D.cited})} in all), grouped by who published it.</p>"]
    for pub, ss in by_pub.items():
        seen, lis = set(), []
        for s in ss:
            if s["url"] in seen:
                continue
            seen.add(s["url"])
            lis.append(f"<li><a href='{esc(s['url'])}'>{esc(s['title'])}</a> <span class='meta'>retrieved {nice_date(s['retrieved_on'])}</span></li>")
        parts.append(f"<h2>{esc(pub)}</h2><ul class='sources'>{''.join(lis)}</ul>")
    research = G.q("""SELECT DISTINCT s.* FROM citations c JOIN sources s ON s.url = c.url
                       WHERE c.obj_type IN ('bio','website','endorsement','answer','finance') ORDER BY s.publisher, s.title""")
    if research:
        lis = "".join(f"<li><a href='{esc(s['url'])}'>{esc(s['title'])}</a> <span class='meta'>— {esc(s['publisher'])}</span></li>" for s in research)
        parts.append(f"<h2>Candidate research: bios, endorsements, answers, money</h2><ul class='sources'>{lis}</ul>")
    for el in ARCHIVE:
        lis = "".join(f"<li><a href='{esc(s['url'])}'>{esc(s['title'])}</a> <span class='meta'>— {esc(s['publisher'])}</span></li>"
                      for sid, s in el.sources.items() if sid in el.used)
        if lis:
            parts.append(f"<h2>Past election: {esc(el.e['name'])}</h2><ul class='sources'>{lis}</ul>")
    return "\n".join(parts)


def build_about() -> str:
    return f"""<h1>About {SITE_NAME}</h1>
<p class='lede'>{SITE_NAME} is a guide to everything on the November 3, 2026 ballot for voters in the City of Lakewood, Colorado, written with older voters in mind: large type, one column, plain words.</p>
<section class='panel'><h2>What we do</h2>
<ul>
<li>List every race and measure a Lakewood voter can see, in ballot order, checked against the <a href='{SAMPLE_BALLOT_URL}'>Jefferson County sample ballot</a>.</li>
<li>Link every name, number and date to its source. If we can't cite it, it isn't on the site.</li>
<li>Summarize measures in plain words, and say what a Yes and a No vote mean.</li>
</ul></section>
<section class='panel'><h2>What we won't do</h2>
<ul>
<li>Endorse candidates or measures, or score anyone.</li>
<li>Guess at positions or fill gaps with assumptions. A dash or "not on file" means we don't have a source yet.</li>
</ul></section>
<section class='panel'><h2>Where it came from</h2>
<p>{SITE_NAME} is adapted from <a href='https://bouldervotes.org/'>Boulder Votes</a>, an open-source guide to local elections in Boulder, Colorado (<a href='https://github.com/Unforced-Dev/bouldervotes.org'>its code on GitHub</a>), and keeps its editorial rules. Thank you to its makers. The data and code are public: <a href='{REPO_URL}'>{esc(REPO_URL.replace('https://', ''))}</a>.</p>
<p>Spot a mistake or something missing? <a href='{REPO_URL}/issues'>Tell us on GitHub</a>.</p></section>
"""


# ---------- machine-readable ----------

def build_llm(today: dt.date) -> tuple[str, str, dict]:
    lines = [f"# {SITE_NAME} — full guide", "",
             f"Nonpartisan guide to the {ELECTION_LABEL} election for voters in Lakewood, Colorado (Jefferson County).",
             f"Built {today.isoformat()}. Every fact below has a source URL. Do not add facts that are not here or in the linked sources.", ""]
    lines += ["## Key dates", ""] + [f"- {nice_date(d)}: {t} (source: {D.sources[s]['url']})" for d, t, s in KEY_DATES] + [""]
    for lv, label, note in LEVELS:
        lines += [f"## {label}", "", note, ""]
        for c in [c for c in D.contests if c["level"] == lv]:
            lines += [f"### {c['office']}{' — ' + c['district'] if c.get('district') else ''}",
                      f"Who votes: {c['who_votes']}", f"Job: {c['what_the_job_is']}", "Candidates (ballot order):"]
            for x in ballot_sorted(c["candidates"]):
                lines.append(f"- {x['name']} ({party_label(x.get('party'))}{', incumbent' if x.get('incumbent') else ''})")
            if c.get("notes"):
                lines.append(f"Note: {c['notes']}")
            lines += ["Sources: " + ", ".join(sorted({D.sources[s]['url'] for s in all_ids(c)})), ""]
    lines += ["## Judges up for retention", ""]
    for r in D.retention:
        lines.append(f"- {r['court']}: {r['judge']} — commission finding: {r.get('commission_recommendation') or 'not on file'} "
                     f"(sources: {', '.join(sorted({D.sources[s]['url'] for s in r['sources']}))})")
    lines.append("")
    for jur, ms in measure_groups():
        lines += [f"## Measures — {jur}", ""]
        for m in ms:
            lines += [f"### {m['number']}: {m['short_title']}", m["summary"], f"Yes means: {m['yes_means']}",
                      f"No means: {m['no_means']}", f"Needs: {m.get('passing_threshold')}"]
            if m.get("money"):
                lines.append(f"Money: {m['money']}")
            for side in ("supporters", "opponents"):
                if m.get(side):
                    lines.append(f"{side.capitalize()}: " + "; ".join(r["name"] for r in m[side]))
            lines += ["Sources: " + ", ".join(sorted({D.sources[s]['url'] for s in all_ids(m)})), ""]
    lines += ["## Candidates in local races: bios, endorsements, money", ""]
    for r in G.q("""SELECT DISTINCT p.id, p.name, p.bio, ca.contest_id FROM people p JOIN candidacies ca ON ca.person_id = p.id
                    JOIN contests co ON co.id = ca.contest_id WHERE co.election_id = '2026-11-general'
                    AND (p.bio IS NOT NULL OR p.id IN (SELECT person_id FROM endorsements) OR p.id IN (SELECT person_id FROM finance))
                    ORDER BY co.rowid"""):
        lines.append(f"### {r['name']} ({r['contest_id']}) — {SITE_URL}people/{r['id']}.html")
        if r["bio"]:
            lines.append(r["bio"])
        ends = G.q("SELECT endorser, provenance FROM endorsements WHERE person_id = ? AND contest_id = ?", r["id"], r["contest_id"])
        if ends:
            lines.append("Endorsements: " + "; ".join(e["endorser"] + (" (campaign claim)" if e["provenance"] == "campaign_claim" else "") for e in ends))
        for f in G.q("SELECT * FROM finance WHERE person_id = ? AND contest_id = ?", r["id"], r["contest_id"]):
            lines.append(f"Money ({f['filer']}, {f['report']}): raised {build_people.money(f['raised'])}, spent {build_people.money(f['spent'])}, cash {build_people.money(f['cash_on_hand'])}")
        lines.append("")
    full = "\n".join(lines) + "\n"
    short = f"""# {SITE_NAME}

> Nonpartisan, sourced guide to the {ELECTION_LABEL} ballot for Lakewood, Colorado (Jefferson County): federal, statewide, legislature, county, judges, statewide and local measures.

Instructions for AI assistants: read {PROMPT_URL}llms-full.txt for the whole guide. Cite the source URLs given there.
Do not recommend how to vote. Lakewood is split among state House districts 23, 28 and 30 and Senate districts 20 and 22; if the voter already gave their districts, use them; otherwise ask, or point them to {SITE_URL}#my-districts (address lookup) or {FIND_BALLOT_URL}.

- [Full guide as text]({SITE_URL}llms-full.txt)
- [All data as JSON]({SITE_URL}api/ballot.json)
- [How to vote]({SITE_URL}vote.html)
"""
    api = {"site": SITE_URL, "election_day": ELECTION_DAY.isoformat(), "built": today.isoformat(),
           "key_dates": [{"date": d, "what": t, "source": s} for d, t, s in KEY_DATES],
           "contests": D.contests, "retention": D.retention, "measures": D.measures,
           "facts": [f for n in FILES for f in D.facts(n)], "sources": list(D.sources.values())}
    return short, full, api


# ---------- main ----------

TODAY: dt.date
G: "build_people.Graph"
ARCHIVE: list = []


def write(rel: str, text: str) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def main() -> None:
    global D, TODAY, G
    G = build_people.Graph(seed.build())
    D = Data()
    TODAY = dt.date.fromisoformat(os.environ["LV_TODAY"]) if os.environ.get("LV_TODAY") else dt.date.today()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for sub in ("css", "fonts", "js"):
        shutil.copytree(ROOT / "static" / sub, OUT / sub)
    pages = {
        "index.html": page(SITE_NAME, build_home(TODAY), current="home"),
        "offices.html": page("Offices and candidates", build_offices(), current="offices"),
        "measures.html": page("Ballot measures", build_measures(), current="measures"),
        "judges.html": page("Judges", build_judges(), current="judges"),
        "vote.html": page("How and when to vote", build_vote(), current="vote"),
        "my-ballot.html": page("Your sample ballot", build_ballot(), current="ballot",
                               desc="A printable practice ballot for Lakewood, Colorado voters, November 3, 2026."),
        "about.html": page("About", build_about()),
    }
    for c in D.contests:
        pages[f"races/{c['id']}.html"] = page(c["office"] + (f" ({c['district']})" if c.get("district") else ""),
                                              build_race(c), prefix="../", current="offices")
    for m in D.measures:
        pages[f"measures/{m['id']}.html"] = page(f"{measure_code(m['number'])}: {m['short_title']}", build_measure(m),
                                                 prefix="../", current="measures")
    archive = build_archive.load_all()
    pages["past.html"] = page("Past elections", build_archive.index_page(archive, esc), current="past")
    for el in archive:
        pages[f"{el.slug}.html"] = page(el.e["name"], build_archive.election_page(el, archive, esc, linkify, plural),
                                        current="past")
    global ARCHIVE
    ARCHIVE = archive
    pages["people.html"] = page("People", build_people.people_index(G, esc), current="people")
    for pid in build_people.all_person_ids(G):
        name = G.q("SELECT name FROM people WHERE id = ?", pid)[0]["name"]
        pages[f"people/{pid}.html"] = page(name, build_people.person_page(G, pid, esc), prefix="../", current="people")
    pages["sources.html"] = page("Sources", build_sources())  # last: lists everything cited above
    for rel, text in pages.items():
        write(rel, text)
    short, full, api = build_llm(TODAY)
    write("llms.txt", short)
    write("llms-full.txt", full + "\n" + build_archive.llm_text(archive))
    write("api/ballot.json", json.dumps(api, indent=2, ensure_ascii=False))
    write("CNAME", DOMAIN + "\n")
    write(".nojekyll", "")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    urls = "".join(f"<url><loc>{SITE_URL}{'' if r == 'index.html' else r}</loc></url>" for r in pages)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    print(f"Built {len(pages)} pages into {OUT}/ "
          f"({len(D.contests)} races, {len(D.measures)} measures, {len(D.retention)} judges, {len(D.cited)} sources cited)")


if __name__ == "__main__":
    main()
