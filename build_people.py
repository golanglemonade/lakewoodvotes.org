"""Person pages (docs/people/<id>.html) and the People index, read from the SQLite graph built by seed.py.

Rules carried over from Boulder Votes:
- Endorsements say who says so: the endorser's own statement, a campaign's claim ("X campaign lists Y"), or a news report.
- Questionnaire answers are the candidate's own words, quoted, with the outlet and a link.
- Money is shown as filed, with the report and date. A dash means we don't have it.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
import re

PROVENANCE = {
    "endorser_statement": "Endorser's own statement",
    "campaign_claim": "Campaign lists",
    "news_report": "News report",
}
KIND_GROUPS = (
    ("organization", "Organizations"),
    ("newspaper", "Newspapers"),
    ("elected", "Current elected officials"),
    ("former_elected", "Former elected officials"),
    ("individual", "Other individuals"),
)



def short_pub(p: str) -> str:
    return re.split(r" \(|, ", p)[0].strip()


class Graph:
    def __init__(self, db_path) -> None:
        self.con = sqlite3.connect(db_path)
        self.con.row_factory = sqlite3.Row

    def q(self, sql: str, *args):
        return self.con.execute(sql, args).fetchall()

    def cites(self, obj_type: str, obj_id) -> list[sqlite3.Row]:
        return self.q("SELECT s.* FROM citations c JOIN sources s ON s.url = c.url WHERE c.obj_type = ? AND c.obj_id = ?",
                      obj_type, str(obj_id))

    def person_for(self, contest_id: str, ballot_name: str) -> list[str]:
        return [r["person_id"] for r in self.q("SELECT person_id FROM candidacies WHERE contest_id = ? AND ballot_name = ?",
                                               contest_id, ballot_name)]

    def summary(self, pid: str, contest_id: str) -> dict:
        n_end = self.q("SELECT count(*) n FROM endorsements WHERE person_id = ? AND contest_id = ?", pid, contest_id)[0]["n"]
        n_ans = self.q("SELECT count(*) n FROM answers WHERE person_id = ? AND contest_id = ?", pid, contest_id)[0]["n"]
        fin = self.q("SELECT * FROM finance WHERE person_id = ? AND contest_id = ? ORDER BY coalesce(raised, 0) DESC LIMIT 1",
                     pid, contest_id)
        person = self.q("SELECT * FROM people WHERE id = ?", pid)[0]
        return {"endorsements": n_end, "answers": n_ans, "finance": fin[0] if fin else None, "bio": person["bio"],
                "researched": bool(person["bio"] or n_end or n_ans or fin)}


def money(v) -> str:
    return "—" if v is None else f"${v:,.0f}"


def _cite(rows, esc) -> str:
    """One link per URL, grouped by publisher: 'Wikipedia (1, 2)'."""
    seen, by = set(), {}
    for s in rows:
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        by.setdefault(short_pub(s["publisher"]), []).append(s)
    parts = []
    for pub, ss in by.items():
        if len(ss) == 1:
            parts.append(f"<a href='{esc(ss[0]['url'])}' title='{esc(ss[0]['title'])}'>{esc(pub)}</a>")
        else:
            nums = ", ".join(f"<a href='{esc(x['url'])}' title='{esc(x['title'])}'>{i}</a>" for i, x in enumerate(ss, 1))
            parts.append(f"{esc(pub)} ({nums})")
    if not parts:
        return ""
    return f"<span class='src'>Source{'s' if len(seen) > 1 else ''}: {'; '.join(parts)}</span>"


def person_page(g: Graph, pid: str, esc, prefix: str = "../") -> str:
    p = g.q("SELECT * FROM people WHERE id = ?", pid)[0]
    runs = g.q("""SELECT ca.*, co.office, co.district, co.page, co.level, e.date, e.name AS election, e.id AS election_id
                  FROM candidacies ca JOIN contests co ON co.id = ca.contest_id JOIN elections e ON e.id = co.election_id
                  WHERE ca.person_id = ? ORDER BY e.date DESC""", pid)
    now = [r for r in runs if r["election_id"] == "2026-11-general"]
    parts = [f"<p class='crumb'><a href='{prefix}people.html'>People</a> › {esc(p['name'])}</p>"]
    kicker = esc(now[0]["party"] or "") if now else "Past candidate"
    parts.append(f"<p class='kicker'>{kicker}</p><h1>{esc(p['name'])}</h1>")
    if now:
        r = now[0]
        where = esc(r["office"]) + (f", {esc(r['district'])}" if r["district"] else "")
        ticket = f" (on the ticket “{esc(r['ballot_name'])}”)" if " / " in r["ballot_name"] else ""
        inc = " Incumbent." if r["incumbent"] else ""
        pos = f" Ballot position {r['ballot_order']}." if r["ballot_order"] else ""
        parts.append(f"<p class='lede'>On the November 3, 2026 ballot for <a href='{prefix}{esc(r['page'])}'>{where}</a>{ticket}.{inc}{pos}</p>")
    if p["bio"]:
        parts.append(f"<section class='panel'><h2>About</h2><p>{esc(p['bio'])}</p><p class='meta'>{_cite(g.cites('bio', pid), esc)}</p>"
                     + (f"<p><a href='{esc(p['website'])}'>Campaign website</a></p>" if p["website"] else "") + "</section>")
    elif p["website"]:
        parts.append(f"<p><a href='{esc(p['website'])}'>Campaign website</a></p>")

    if now:
        cid = now[0]["contest_id"]
        ends = g.q("SELECT * FROM endorsements WHERE person_id = ? AND contest_id = ? ORDER BY endorser", pid, cid)
        if ends:
            by = defaultdict(list)
            for e in ends:
                by[e["kind"]].append(e)
            blocks = []
            for kind, label in KIND_GROUPS:
                if not by.get(kind):
                    continue
                lis = []
                for e in by[kind]:
                    title = f", {esc(e['title'])}" if e["title"] else ""
                    if e["provenance"] == "campaign_claim":
                        text = f"{esc(p['name'])} campaign lists <strong>{esc(e['endorser'])}</strong>{title}"
                    else:
                        text = f"<strong>{esc(e['endorser'])}</strong>{title} <span class='pill'>{esc(PROVENANCE[e['provenance']])}</span>"
                    lis.append(f"<li>{text} {_cite(g.cites('endorsement', e['id']), esc)}</li>")
                blocks.append(f"<h3>{label} <span class='count'>({len(by[kind])})</span></h3><ul class='edges'>{''.join(lis)}</ul>")
            parts.append("<section class='panel'><h2 id='endorsements'>Endorsements</h2>"
                         "<p class='note'>Labels say who says so. “Endorser's own statement” means the group or person announced it. "
                         "“Campaign lists” means only the candidate's campaign says so. Titles are as printed on the cited page; titles on a campaign's list are the campaign's wording and may be out of date. "
                         "This is not a complete list and not our recommendation.</p>" + "".join(blocks) + "</section>")
        ans = g.q("SELECT * FROM answers WHERE person_id = ? AND contest_id = ?", pid, cid)
        if ans:
            items = "".join(f"<div class='qa'><p class='q'><span class='meta'>{esc(a['outlet'])} asked:</span> {esc(a['question'])}</p>"
                            f"<blockquote class='answer'>{esc(a['answer'])}</blockquote><p class='meta'>{_cite(g.cites('answer', a['id']), esc)}</p></div>"
                            for a in ans)
            parts.append("<section class='panel'><h2 id='answers'>In their own words</h2>"
                         "<p class='note'>Quoted from published candidate questionnaires and voter guides. “…” marks where we shortened an answer; follow the link for the full text.</p>"
                         f"{items}</section>")
        fins = g.q("SELECT * FROM finance WHERE person_id = ? AND contest_id = ? ORDER BY period_end DESC", pid, cid)
        if fins:
            rows = "".join(f"<tr><td>{esc(f['committee'] or '—')}<br><span class='meta'>{esc(f['report'] or '')}"
                           f"{' · period ending ' + esc(f['period_end']) if f['period_end'] else ''}</span>"
                           f"{'<br><span class=meta>' + esc(f['notes']) + '</span>' if f['notes'] else ''}</td>"
                           f"<td class='num'>{money(f['raised'])}</td><td class='num'>{money(f['spent'])}</td><td class='num'>{money(f['cash_on_hand'])}</td>"
                           f"<td>{_cite(g.cites('finance', f['id']), esc)}</td></tr>" for f in fins)
            filer = "Federal Election Commission" if fins[0]["filer"] == "FEC" else "Colorado Secretary of State (TRACER)"
            parts.append(f"<section class='panel'><h2 id='money'>Campaign money</h2><p class='note'>As filed with the {filer}. "
                         "Totals are for the whole campaign so far, as of the report shown. A dash means the report we found doesn't give that figure.</p>"
                         "<div class='table-scroll'><table><thead><tr><th>Committee and report</th><th class='num'>Raised</th>"
                         f"<th class='num'>Spent</th><th class='num'>Cash on hand</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div></section>")
        if not (p["bio"] or ends or ans or fins):
            parts.append("<p class='note'>We haven't gathered a bio, endorsements, questionnaire answers or campaign money for this candidate yet. "
                         "For now we cover those for the local races: Congress District 7, the state legislature and Jefferson County.</p>")

    past = [r for r in runs if r["election_id"] != "2026-11-general"]
    if past:
        rows = []
        for r in past:
            res = "Won" if r["won"] else "Did not win"
            votes = f"{r['votes']:,}" if r["votes"] is not None else "—"
            pct = f"{r['pct']:.1f}%" if r["pct"] is not None else "—"
            office = esc(r["office"]) + (f" — {esc(r['district'])}" if r["district"] else "")
            rows.append(f"<tr{' class=won' if r['won'] else ''}><td><a href='{prefix}{esc(r['page'])}'>{esc(r['election'])}</a></td>"
                        f"<td>{office}</td><td>{esc(r['party'] or 'Nonpartisan')}</td><td class='num'>{votes}</td><td class='num'>{pct}</td><td>{res}</td></tr>")
        parts.append("<section class='panel'><h2 id='history'>On the ballot before</h2>"
                     "<div class='table-scroll'><table><thead><tr><th>Election</th><th>Office</th><th>Party</th><th class='num'>Votes</th>"
                     f"<th class='num'>Share</th><th>Result</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
                     "<p class='note'>Counts are as reported on each election's page, with its sources.</p></section>")

    used = g.q("""SELECT DISTINCT s.* FROM citations c JOIN sources s ON s.url = c.url
                  WHERE (c.obj_type IN ('bio','website') AND c.obj_id = ?)
                     OR (c.obj_type = 'candidacy' AND c.obj_id LIKE ?)
                     OR (c.obj_type = 'endorsement' AND c.obj_id IN (SELECT CAST(id AS TEXT) FROM endorsements WHERE person_id = ?))
                     OR (c.obj_type = 'answer' AND c.obj_id IN (SELECT CAST(id AS TEXT) FROM answers WHERE person_id = ?))
                     OR (c.obj_type = 'finance' AND c.obj_id IN (SELECT CAST(id AS TEXT) FROM finance WHERE person_id = ?))
                  ORDER BY s.publisher, s.title""", pid, f"%|{pid}", pid, pid, pid)
    if used:
        lis = "".join(f"<li><a href='{esc(s['url'])}'>{esc(s['title'])}</a> <span class='meta'>— {esc(s['publisher'])}</span></li>" for s in used)
        parts.append(f"<section class='panel'><h2>Sources</h2><ul class='sources'>{lis}</ul></section>")
    return "\n".join(parts)


def people_index(g: Graph, esc) -> str:
    parts = ["<h1>People</h1>",
             "<p class='lede'>Everyone on the 2026 ballot, and everyone who ran in the past elections in this guide. "
             "Open a name for their bio, endorsements, answers, campaign money and past races, where we have them.</p>"]
    rows = g.q("""SELECT co.id, co.office, co.district, co.page, ca.person_id, p.name, ca.party, ca.incumbent
                  FROM candidacies ca JOIN contests co ON co.id = ca.contest_id JOIN people p ON p.id = ca.person_id
                  WHERE co.election_id = '2026-11-general' ORDER BY co.rowid, ca.ballot_order, p.name""")
    by = defaultdict(list)
    order = []
    for r in rows:
        if r["id"] not in by:
            order.append(r)
        by[r["id"]].append(r)
    cards = []
    for c in order:
        lis = "".join(f"<li><a href='people/{esc(r['person_id'])}.html'>{esc(r['name'])}</a> "
                      f"<span class='party'>({esc(r['party'] or '—')}{', incumbent' if r['incumbent'] else ''})</span></li>" for r in by[c["id"]])
        title = esc(c["office"]) + (f" — {esc(c['district'])}" if c["district"] else "")
        cards.append(f"<article class='card'><h3><a href='{esc(c['page'])}'>{title}</a></h3><ul class='plain'>{lis}</ul></article>")
    parts.append(f"<h2>On the 2026 ballot</h2><div class='archive-grid'>{''.join(cards)}</div>")
    past = g.q("""SELECT p.id, p.name, max(e.date) last, group_concat(DISTINCT substr(e.date,1,4)) years
                  FROM people p JOIN candidacies ca ON ca.person_id = p.id JOIN contests co ON co.id = ca.contest_id
                  JOIN elections e ON e.id = co.election_id
                  WHERE p.id NOT IN (SELECT person_id FROM candidacies c2 JOIN contests k ON k.id = c2.contest_id WHERE k.election_id = '2026-11-general')
                  GROUP BY p.id ORDER BY p.name""")
    lis = "".join(f"<li><a href='people/{esc(r['id'])}.html'>{esc(r['name'])}</a> <span class='meta'>({esc(r['years'])})</span></li>" for r in past)
    parts.append(f"<h2>Past candidates</h2><ul class='people-cols'>{lis}</ul>")
    return "\n".join(parts)


def all_person_ids(g: Graph) -> list[str]:
    return [r["id"] for r in g.q("SELECT id FROM people WHERE id IN (SELECT person_id FROM candidacies) ORDER BY id")]
