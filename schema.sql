-- Lakewood Votes evidence graph (SQLite). Rebuilt from the committed JSON in data/ by seed.py on every build;
-- the .db file is not committed. People persist across elections; everything published points at a source.

PRAGMA foreign_keys = ON;

CREATE TABLE sources (
  url          TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  publisher    TEXT NOT NULL,
  retrieved_on TEXT NOT NULL
);

CREATE TABLE elections (
  id    TEXT PRIMARY KEY,          -- '2026-11-general', '2024-11-general', '2023-11-lakewood', ...
  date  TEXT NOT NULL,
  name  TEXT NOT NULL,
  page  TEXT NOT NULL              -- site path: 'index.html', '2024.html', ...
);

CREATE TABLE people (
  id       TEXT PRIMARY KEY,       -- slug
  name     TEXT NOT NULL,          -- display name (latest ballot name)
  bio      TEXT,
  website  TEXT
);

CREATE TABLE person_names (        -- every spelling we have seen; used to join people across years
  name      TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES people(id)
);

CREATE TABLE contests (
  id          TEXT PRIMARY KEY,
  election_id TEXT NOT NULL REFERENCES elections(id),
  level       TEXT NOT NULL,
  office      TEXT NOT NULL,
  district    TEXT,
  page        TEXT NOT NULL        -- where the contest is shown
);

CREATE TABLE candidacies (
  contest_id    TEXT NOT NULL REFERENCES contests(id),
  person_id     TEXT NOT NULL REFERENCES people(id),
  ballot_name   TEXT NOT NULL,     -- the full ballot line, e.g. a governor/lt. governor ticket
  party         TEXT,
  incumbent     INTEGER,
  ballot_order  INTEGER,
  votes         INTEGER,           -- NULL for 2026 (not decided yet)
  pct           REAL,
  won           INTEGER,
  PRIMARY KEY (contest_id, person_id)
);

CREATE TABLE endorsements (
  id          INTEGER PRIMARY KEY,
  person_id   TEXT NOT NULL REFERENCES people(id),
  contest_id  TEXT NOT NULL REFERENCES contests(id),
  endorser    TEXT NOT NULL,
  kind        TEXT NOT NULL CHECK (kind IN ('organization','elected','former_elected','individual','newspaper')),
  title       TEXT,
  provenance  TEXT NOT NULL CHECK (provenance IN ('endorser_statement','campaign_claim','news_report'))
);

CREATE TABLE answers (
  id          INTEGER PRIMARY KEY,
  person_id   TEXT NOT NULL REFERENCES people(id),
  contest_id  TEXT NOT NULL REFERENCES contests(id),
  outlet      TEXT NOT NULL,
  question    TEXT NOT NULL,
  answer      TEXT NOT NULL,
  topic       TEXT
);

CREATE TABLE finance (
  id           INTEGER PRIMARY KEY,
  person_id    TEXT NOT NULL REFERENCES people(id),
  contest_id   TEXT NOT NULL REFERENCES contests(id),
  committee    TEXT,
  filer        TEXT NOT NULL,      -- 'TRACER' (Colorado SOS) or 'FEC'
  report       TEXT,
  period_end   TEXT,
  raised       REAL,
  spent        REAL,
  cash_on_hand REAL,
  notes        TEXT
);

-- Citations for any row above: (table, row key) -> source url.
CREATE TABLE citations (
  obj_type  TEXT NOT NULL,         -- 'bio' | 'website' | 'endorsement' | 'answer' | 'finance' | 'candidacy'
  obj_id    TEXT NOT NULL,
  url       TEXT NOT NULL REFERENCES sources(url),
  PRIMARY KEY (obj_type, obj_id, url)
);
