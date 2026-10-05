#!/usr/bin/env python3
"""
One-off: pull river length (P2043) statements recorded in units other than
kilometre. Kilometre alone covers 61,440 of 61,990 rivers with a length
statement (99.1%) -- the remaining ~640 statements (some rivers have both
a km and a non-km statement, hence 640 > the 550 unique-item gap) use
metre (304) or mile (336); no rivers use foot/mm/cm (checked, all zero).

wikidata_size.py's PROPERTIES config only supports one canonical_unit per
property, so this reuses the same engine (wikidata_common) directly rather
than hacking that config for a one-off two-unit sweep.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base import write_raw_facts
from wikidata_common import ingest_property, polite_sleep

OUT_PATH = Path(__file__).parent / "data" / "raw" / "wikidata_size.jsonl"
RIVER_CLASS = "Q4022"
METRE = "Q11573"
MILE = "Q253276"

if __name__ == "__main__":
    retrieved_at = datetime.now(timezone.utc).isoformat()
    for unit in (METRE, MILE):
        print(f"--- P2043 (length), river, unit={unit} ---", file=sys.stderr)
        facts = ingest_property(
            pid="P2043",
            label="length",
            dimension="distance",
            entity_class=RIVER_CLASS,
            canonical_unit=unit,
            limit_per_property=1000,
            retrieved_at=retrieved_at,
        )
        written = write_raw_facts(facts, OUT_PATH)
        print(f"    -> {len(facts)} facts fetched, {written} new rows written", file=sys.stderr)
        polite_sleep(3.5)
    print(f"Done. Output: {OUT_PATH}", file=sys.stderr)
