# Operating Lakewood Votes

## Adding or fixing a fact

1. Edit the right file in `data/2026/`. Add the document to that file's `sources` first (`id`, `title`, `publisher`, `url`, `retrieved_on`), then cite its `id` in the item's `sources`.
2. `python3 build.py && python3 -m unittest`.
3. Commit and push to `main`; Pages rebuilds in about a minute.

Rules: no fact without a source; summaries in plain words, not copied; supporters/opponents only when a source names them; party and incumbency are facts, characterizations are not. Unconfirmed items go in `open_questions`, not on the site.

## Ballot order

Candidates render in `ballot_order`, taken from the Jefferson County sample ballot (and the SOS ballot-order table for legislative races).

## After the election

Add results to the contest and measure entries (with the county's official results as the source) and start a `data/2027/` folder for the city mayor and council races.
