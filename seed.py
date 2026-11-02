"""Build data/lakewoodvotes.db from the committed JSON (data/2026, data/archive, data/people).

The JSON is the record; the database is a rebuildable index for cross-year questions
("everything this person has run for", "who endorsed whom"). Nothing is typed in here
except NAME_MERGES: the explicit, sourced decisions that two spellings are one person.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "lakewoodvotes.db"

# Spellings that are the same person, each backed by a source in the people files' aka lists
# or by the same exact name on two ballots. Exact-name matches merge automatically; list
# anything else here with the reason.
NAME_MERGES = {
    "Dave Rein": "David Rein",                      # Lakewood Ward 4 (2023) = HD-28 candidate; see people_legislature.json
    "Monica Duran": "Monica Irasema Duran",
}


# Same name on two ballots, but we have no source saying it is the same person (different parties).
# These stay separate people; the past-election one gets a year suffix.
NOT_MERGED: set[str] = set()  # Blake Huber and T.J. Cole were checked: same people (see people_statewide_a.json)


def slug(s: str) -> str:
    s = re.sub(r"[\"'()]", "", s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def split_ticket(name: str) -> list[str]:
    return [p.strip() for p in name.split(" / ")] if " / " in name else [name]


class Seeder:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con
        self.names: dict[str, str] = {}   # spelling -> person id

    def source(self, s: dict) -> None:
        self.con.execute("INSERT OR IGNORE INTO sources VALUES (?,?,?,?)",
                         (s["url"], s["title"], s["publisher"], s["retrieved_on"]))

    def cite(self, obj_type: str, obj_id, ids, srcs: dict) -> None:
        for sid in ids or []:
            self.con.execute("INSERT OR IGNORE INTO citations VALUES (?,?,?)", (obj_type, str(obj_id), srcs[sid]["url"]))

    def person(self, name: str) -> str:
        name = NAME_MERGES.get(name, name)
        if name in self.names:
            return self.names[name]
        pid = slug(name)
        self.con.execute("INSERT OR IGNORE INTO people (id, name) VALUES (?,?)", (pid, name))
        self.names[name] = pid
        self.con.execute("INSERT OR IGNORE INTO person_names VALUES (?,?)", (name, pid))
        return pid

    def alias(self, alias: str, pid: str) -> None:
        self.names.setdefault(alias, pid)
        self.con.execute("INSERT OR IGNORE INTO person_names VALUES (?,?)", (alias, pid))


def build() -> Path:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((ROOT / "schema.sql").read_text())
    sd = Seeder(con)

    # 2026: aliases first so later spellings land on the same person.
    people_files = [json.loads(p.read_text()) for p in sorted((ROOT / "data" / "people").glob("*.json"))]
    for pf in people_files:
        for p in pf["people"]:
            pid = sd.person(p["name"])
            for a in p.get("aka") or []:
                sd.alias(NAME_MERGES.get(a, a), pid)
                sd.alias(a, pid)

    con.execute("INSERT INTO elections VALUES ('2026-11-general','2026-11-03','November 3, 2026 general election','index.html')")
    for name in ("federal_statewide", "legislature", "county_judicial"):
        d = json.loads((ROOT / "data" / "2026" / f"{name}.json").read_text())
        srcs = {s["id"]: s for s in d["sources"]}
        for s in d["sources"]:
            sd.source(s)
        for c in d.get("contests", []):
            con.execute("INSERT INTO contests VALUES (?,?,?,?,?,?)",
                        (c["id"], "2026-11-general", c["level"], c["office"], c.get("district"), f"races/{c['id']}.html"))
            for x in c["candidates"]:
                for nm in split_ticket(x["name"]):
                    pid = sd.person(nm)
                    con.execute("INSERT INTO candidacies VALUES (?,?,?,?,?,?,NULL,NULL,NULL)",
                                (c["id"], pid, x["name"], x.get("party"), int(bool(x.get("incumbent"))), x.get("ballot_order")))
                    sd.cite("candidacy", f"{c['id']}|{pid}", x.get("sources"), srcs)
                    if x.get("website"):
                        con.execute("UPDATE people SET website = coalesce(website, ?) WHERE id = ?", (x["website"], pid))

    # Past elections.
    for p in sorted((ROOT / "data" / "archive").glob("*.json")):
        d = json.loads(p.read_text())
        e = d["election"]
        y, m = e["date"][:4], int(e["date"][5:7])
        page = f"{y}.html" if m == 11 else f"{y}-{['', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'][m]}.html"
        con.execute("INSERT INTO elections VALUES (?,?,?,?)", (e["id"], e["date"], e["name"], page))
        srcs = {s["id"]: s for s in d["sources"]}
        for s in d["sources"]:
            sd.source(s)
        for c in d.get("contests", []):
            con.execute("INSERT INTO contests VALUES (?,?,?,?,?,?)",
                        (c["id"], e["id"], c["level"], c["office"], c.get("district"), f"{page}#{c['level']}"))
            for x in c["candidates"]:
                for nm in split_ticket(x["name"]):
                    clean = re.sub(r"\s*\((write-in|incumbent)\)$", "", nm)
                    if clean in NOT_MERGED:
                        pid = slug(clean) + "-" + y
                        con.execute("INSERT OR IGNORE INTO people (id, name) VALUES (?,?)", (pid, clean))
                    else:
                        pid = sd.person(clean)
                    con.execute("INSERT OR IGNORE INTO candidacies VALUES (?,?,?,?,?,?,?,?,?)",
                                (c["id"], pid, x["name"], x.get("party"), int(bool(x.get("incumbent"))), None,
                                 x.get("votes"), x.get("pct"), int(bool(x.get("won")))))
                    sd.cite("candidacy", f"{c['id']}|{pid}", c.get("sources"), srcs)

    # Candidate research: bios, endorsements, answers, money.
    for pf in people_files:
        srcs = {s["id"]: s for s in pf["sources"]}
        for s in pf["sources"]:
            sd.source(s)
        for p in pf["people"]:
            pid = sd.person(p["name"])
            if p.get("bio"):
                con.execute("UPDATE people SET bio = ? WHERE id = ?", (p["bio"], pid))
                sd.cite("bio", pid, p.get("bio_sources"), srcs)
            if p.get("website"):
                con.execute("UPDATE people SET website = ? WHERE id = ?", (p["website"], pid))
                sd.cite("website", pid, p.get("website_sources"), srcs)
            for en in p.get("endorsements") or []:
                cur = con.execute("INSERT INTO endorsements (person_id, contest_id, endorser, kind, title, provenance) VALUES (?,?,?,?,?,?)",
                                  (pid, p["contest_id"], en["endorser"], en["kind"], en.get("title"), en["provenance"]))
                sd.cite("endorsement", cur.lastrowid, en.get("sources"), srcs)
            for a in p.get("answers") or []:
                cur = con.execute("INSERT INTO answers (person_id, contest_id, outlet, question, answer, topic) VALUES (?,?,?,?,?,?)",
                                  (pid, p["contest_id"], a["outlet"], a["question"], a["answer"], a.get("topic")))
                sd.cite("answer", cur.lastrowid, a.get("sources"), srcs)
            for f in p.get("finance") or []:
                cur = con.execute("INSERT INTO finance (person_id, contest_id, committee, filer, report, period_end, raised, spent, cash_on_hand, notes) "
                                  "VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  (pid, p["contest_id"], f.get("committee"), f["filer"], f.get("report"), f.get("period_end"),
                                   f.get("raised_total"), f.get("spent_total"), f.get("cash_on_hand"), f.get("notes")))
                sd.cite("finance", cur.lastrowid, f.get("sources"), srcs)
    con.commit()
    return DB


if __name__ == "__main__":
    path = build()
    con = sqlite3.connect(path)
    for t in ("people", "candidacies", "endorsements", "answers", "finance", "sources"):
        print(t, con.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
