"""Editorial rules, enforced: every fact has a source, every source resolves, no broken local links."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "2026"
FILES = ("federal_statewide", "state_measures", "legislature", "county_judicial", "local_and_voting")


def load():
    return {n: json.loads((DATA / f"{n}.json").read_text()) for n in FILES}


class TestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = load()
        cls.sources = {}
        for d in cls.files.values():
            for s in d["sources"]:
                cls.sources.setdefault(s["id"], s)

    def items(self):
        for name, d in self.files.items():
            for c in d.get("contests", []):
                yield name, f"contest {c['id']}", c
                for x in c["candidates"]:
                    yield name, f"candidate {x['name']}", x
            for kind in ("retention", "measures"):
                for r in d.get(kind, []):
                    yield name, f"{kind} {r['id']}", r
            for f in d.get("facts", []):
                yield name, f"fact {f['key']}", f

    def test_every_item_has_a_source(self):
        for name, label, item in self.items():
            with self.subTest(file=name, item=label):
                self.assertTrue(item.get("sources"), "no sources")

    def test_every_source_id_resolves(self):
        for name, label, item in self.items():
            for sid in item.get("sources", []):
                with self.subTest(file=name, item=label, source=sid):
                    self.assertIn(sid, self.sources)
        for d in self.files.values():
            for m in d.get("measures", []):
                for side in ("supporters", "opponents"):
                    for r in m.get(side) or []:
                        with self.subTest(measure=m["id"], who=r["name"]):
                            self.assertTrue(r.get("sources"))
                            for sid in r["sources"]:
                                self.assertIn(sid, self.sources)

    def test_source_shape(self):
        for sid, s in self.sources.items():
            with self.subTest(source=sid):
                self.assertTrue(s["url"].startswith("https://"), s["url"])
                self.assertRegex(s["retrieved_on"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertTrue(s["title"] and s["publisher"])

    def test_ids_unique(self):
        ids = [c["id"] for d in self.files.values() for k in ("contests", "measures", "retention") for c in d.get(k, [])]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ballot_order_unique_per_race(self):
        for d in self.files.values():
            for c in d.get("contests", []):
                order = [x["ballot_order"] for x in c["candidates"] if x.get("ballot_order") is not None]
                with self.subTest(race=c["id"]):
                    self.assertEqual(len(order), len(set(order)))


DOCS = Path(tempfile.mkdtemp(prefix="lv-test-docs-"))  # never overwrite your docs/ (e.g. a local-testing build)


class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, cwd=ROOT,
                       env={"LV_TODAY": "2026-10-09", "LV_OUT": str(DOCS), "PATH": "/usr/bin:/bin"}, capture_output=True)

    def test_no_broken_local_links(self):
        docs = DOCS
        broken = []
        for page in docs.rglob("*.html"):
            for href in re.findall(r"""href=['"]([^'"]+)['"]""", page.read_text()):
                if href.startswith(("http", "mailto:", "#", "/")):
                    continue
                target = (page.parent / href.split("#")[0].split("?")[0]).resolve()
                if not target.exists():
                    broken.append(f"{page.relative_to(docs)} -> {href}")
        self.assertEqual(broken, [])

    def test_every_race_and_measure_has_a_page(self):
        files = load()
        for d in files.values():
            for c in d.get("contests", []):
                self.assertTrue((DOCS / "races" / f"{c['id']}.html").exists())
            for m in d.get("measures", []):
                self.assertTrue((DOCS / "measures" / f"{m['id']}.html").exists())

    def test_cname(self):
        self.assertEqual((DOCS / "CNAME").read_text().strip(), "lakewoodvotes.org")

    def test_no_boulder_leftovers(self):
        """Boulder Votes is credited by name; Boulder-specific content must not leak in.
        (Endorser titles like "Boulder County Clerk" are real data and allowed.)"""
        for page in (DOCS).rglob("*.html"):
            text = page.read_text()
            with self.subTest(page=str(page)):
                for leftover in ("City of Boulder", "bouldercolorado.gov", "Boulder city ballot", "Boulder County Elections"):
                    self.assertNotIn(leftover, text)
                if "Boulder Votes" in text:
                    self.assertIn("bouldervotes.org", text)

if __name__ == "__main__":
    unittest.main()


class TestArchive(unittest.TestCase):
    def test_archive_sources_resolve_and_counts_are_numbers(self):
        for p in sorted((ROOT / "data" / "archive").glob("*.json")):
            d = json.loads(p.read_text())
            ids = {s["id"] for s in d["sources"]}
            items = [d["election"]] + d.get("contests", []) + d.get("measures", []) + d.get("facts", [])
            for it in items:
                with self.subTest(file=p.name, item=it.get("id") or it.get("key")):
                    self.assertTrue(it.get("sources"), "no sources")
                    self.assertTrue(set(it["sources"]) <= ids, set(it["sources"]) - ids)
            for c in d.get("contests", []):
                for x in c["candidates"]:
                    self.assertTrue(x.get("votes") is None or isinstance(x["votes"], int), (c["id"], x["name"]))
            for m in d.get("measures", []):
                for k in ("yes_votes", "no_votes"):
                    self.assertTrue(m.get(k) is None or isinstance(m[k], int), (m["id"], k))


class TestPeople(unittest.TestCase):
    """Candidate research (data/people/*.json): the Boulder Votes evidence rules."""

    @classmethod
    def setUpClass(cls):
        cls.files = {p.name: json.loads(p.read_text()) for p in sorted((ROOT / "data" / "people").glob("*.json"))}
        cls.ballot = {}
        for d in load().values():
            for c in d.get("contests", []):
                cls.ballot[c["id"]] = {n for x in c["candidates"] for n in [x["name"], *x["name"].split(" / ")]}

    def test_people_match_the_ballot(self):
        for fname, d in self.files.items():
            for p in d["people"]:
                with self.subTest(file=fname, person=p["name"]):
                    self.assertIn(p["contest_id"], self.ballot)
                    self.assertIn(p["name"], self.ballot[p["contest_id"]])

    def test_everything_cited(self):
        for fname, d in self.files.items():
            ids = {s["id"] for s in d["sources"]}
            for p in d["people"]:
                if p.get("bio"):
                    self.assertTrue(p.get("bio_sources"), (fname, p["name"], "bio"))
                if p.get("website"):
                    self.assertTrue(p.get("website_sources"), (fname, p["name"], "website"))
                for key in ("bio_sources", "website_sources"):
                    self.assertTrue(set(p.get(key) or []) <= ids, (fname, p["name"], key))
                for kind in ("endorsements", "answers", "finance"):
                    for it in p.get(kind) or []:
                        with self.subTest(file=fname, person=p["name"], kind=kind):
                            self.assertTrue(it.get("sources"))
                            self.assertTrue(set(it["sources"]) <= ids, set(it["sources"]) - ids)

    def test_endorsement_labels(self):
        for d in self.files.values():
            for p in d["people"]:
                for e in p.get("endorsements") or []:
                    self.assertIn(e["provenance"], {"endorser_statement", "campaign_claim", "news_report"})
                    self.assertIn(e["kind"], {"organization", "elected", "former_elected", "individual", "newspaper"})

    def test_answers_are_short_quotes(self):
        for d in self.files.values():
            for p in d["people"]:
                for a in p.get("answers") or []:
                    with self.subTest(person=p["name"], q=a["question"][:40]):
                        self.assertLessEqual(len(a["answer"].split()), 100)
                        self.assertTrue(a["outlet"] and a["question"])

    def test_money_is_numbers(self):
        for d in self.files.values():
            for p in d["people"]:
                for f in p.get("finance") or []:
                    for k in ("raised_total", "spent_total", "cash_on_hand"):
                        self.assertTrue(f.get(k) is None or isinstance(f[k], (int, float)), (p["name"], k))
                    self.assertIn(f["filer"], {"TRACER", "FEC"})
