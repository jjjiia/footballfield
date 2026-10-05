#!/usr/bin/env python3
"""
Shared Wikidata ingestion engine
---------------------------------
The query/retry/dedup machinery used by every per-theme ingestion script
(wikidata_people.py, wikidata_size.py, ...). Each theme script just defines
its own PROPERTIES dict and a default output path, then calls run_cli().

Design note: this queries the live SPARQL endpoint per property rather than
downloading/parsing the full ~30GB dump. Each theme's property list is small
and curated, so paginated live queries are simpler to iterate on -- and a
naive "GROUP BY unit over the whole property" query times out for
high-volume properties on the public endpoint. The pattern used here
(fetch item ids with a plain wdt: lookup, then re-query with those ids
bound via VALUES) avoids that timeout -- see infinite-facts-project-
plan.md for how this was worked out.

Units are stored as-is (unit_qid + unit_label) per fact, not converted to
a canonical unit here -- real data showed properties mixing units (e.g.
mass in both kg and Jupiter masses), so canonicalization is deferred to
enrichment (Phase 2), once each unit's own P2370 "conversion to SI unit"
factor is looked up.

Requires: no third-party packages (uses urllib from the standard library)
"""

import argparse
import json
import random
import socket
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base import RawFact, write_raw_facts

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "InfiniteFactsProject/0.1 (personal, non-commercial research project)"
BATCH_SIZE = 200  # items per VALUES-bound batch query


def sparql(query, timeout=60, retries=4):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(url, headers={
        "Accept": "application/sparql-results+json",
        "User-Agent": USER_AGENT,
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # A real rate-limit signal, not a transient hiccup -- means
                # "slow down," so this needs a much longer backoff than a
                # gateway error, honoring Retry-After when the server sends one.
                if attempt == retries - 1:
                    raise
                retry_after = e.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else 15 * (attempt + 1)
                time.sleep(wait + random.uniform(0, 3))
            elif e.code in (502, 503, 504):
                # Transient gateway/load hiccups on the public endpoint, not
                # query bugs -- worth a quick retry. Anything else (400 bad
                # syntax, etc.) is a real error, raised immediately instead
                # of masked by a retry loop.
                if attempt == retries - 1:
                    raise
                time.sleep(2 * (attempt + 1) + random.uniform(0, 1))
            else:
                raise
        except (socket.timeout, urllib.error.URLError) as e:
            # Plain read timeouts happen under public-endpoint load too,
            # same treatment as a transient gateway error.
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1) + random.uniform(0, 1))


def polite_sleep(base_seconds):
    time.sleep(base_seconds + random.uniform(0, base_seconds * 0.5))


def fetch_item_ids(pid, limit, entity_class=None, canonical_unit=None):
    """Fast lookup of candidate items, in three modes:

    - entity_class + canonical_unit: scopes to the class AND requires one
      specific unit, then sorts by magnitude. Needed wherever a plain
      magnitude sort was verified to break on mixed units (e.g. mountain
      elevation in both feet and metres). Goes through the reified-statement
      join (p:/psv:/wikibase:quantityUnit), which is only affordable because
      entity_class already bounds the candidate set to a few hundred/
      thousand rows.
    - entity_class only: scopes to the class and sorts by magnitude via the
      plain wdt: predicate. Fast, but only valid where units don't mix
      (verified case-by-case, not assumed).
    - neither: unscoped, unsorted lookup (whatever Wikidata returns first).
      Fine for schema/format testing, not for picking "the biggest X."

    Sorting by magnitude across a property's *entire* range (no class
    filter) isn't attempted here -- it times out on the public endpoint for
    high-volume properties, since it requires a full scan before LIMIT
    applies.

    Some items carry multiple statements with no unique preferred rank
    (e.g. Everest has 4 slightly different elevation values on file), so
    the same item can appear more than once in raw results; deduped here,
    keeping the (highest-magnitude, since results are ORDER BY DESC) first
    occurrence.

    Placeholder sentinel values (e.g. 99999999, used on Wikidata as an
    "unknown/not applicable" filler for some properties -- clinical trial
    participant counts are a known offender) are excluded, since a plain
    magnitude sort otherwise puts them straight at the top ahead of any
    real data."""
    PLACEHOLDER_VALUES = "99999999, 9999999, 999999999, -1"

    # Property pattern comes first, class filter second: Blazegraph's query
    # planner is sensitive to pattern order, and for a huge class like
    # "human" (Q5, ~10M+ items), filtering by class first before joining to
    # the (usually far rarer) property times out. Starting from the
    # property narrows the candidate set immediately regardless of class size.
    if entity_class and canonical_unit:
        query = f"""
        SELECT ?item WHERE {{
          ?item p:{pid} ?stmt .
          ?stmt psv:{pid} ?valueNode .
          ?valueNode wikibase:quantityAmount ?v ;
                     wikibase:quantityUnit wd:{canonical_unit} .
          ?item wdt:P31 wd:{entity_class} .
          FILTER(?v NOT IN ({PLACEHOLDER_VALUES}))
        }}
        ORDER BY DESC(?v)
        LIMIT {limit}
        """
    elif entity_class:
        query = f"""
        SELECT ?item WHERE {{
          ?item wdt:{pid} ?v .
          ?item wdt:P31 wd:{entity_class} .
          FILTER(?v NOT IN ({PLACEHOLDER_VALUES}))
        }}
        ORDER BY DESC(?v)
        LIMIT {limit}
        """
    else:
        query = f"SELECT ?item WHERE {{ ?item wdt:{pid} ?v . }} LIMIT {limit}"

    data = sparql(query)
    seen = set()
    result = []
    for row in data["results"]["bindings"]:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        if qid not in seen:
            seen.add(qid)
            result.append(qid)
    return result


def fetch_claims(pid, item_qids):
    """Join to units/amounts/labels/dates only for these explicit items
    (VALUES-bound) -- this optimizes far better on Blazegraph than a
    nested LIMIT subquery joined straight into the reified-statement path."""
    values_clause = " ".join(f"wd:{q}" for q in item_qids)
    # Some items carry several dated statements for the same property (e.g.
    # population, or an airport's yearly patronage figures) with no
    # "preferred" rank set to mark which is current -- wdt: (truthy) returns
    # all of them in that case, not just one.
    #
    # This used to filter down to just the most-recently-dated statement
    # server-side via a FILTER NOT EXISTS self-join, but that pattern turned
    # out to be pathologically slow for some properties regardless of batch
    # size (patronage: even a 56-item batch timed out at 40s+, most likely
    # because airports report decades of yearly figures, making the
    # self-join expensive per item). Fetching all dated statements and
    # deduping client-side in dedup_facts_per_entity (which already existed
    # for the "several undated ties" case, e.g. Everest's elevation) avoids
    # that expensive query shape entirely.
    query = f"""
    SELECT ?item ?itemLabel ?stmt ?amount ?unit ?unitLabel ?pointInTime WHERE {{
      VALUES ?item {{ {values_clause} }}
      ?item p:{pid} ?stmt .
      ?stmt psv:{pid} ?valueNode .
      ?valueNode wikibase:quantityAmount ?amount ;
                 wikibase:quantityUnit ?unit .
      OPTIONAL {{ ?stmt pq:P585 ?pointInTime . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    data = sparql(query)
    return data["results"]["bindings"]


def format_point_in_time(value):
    """Wikidata time literals look like '2010-01-01T00:00:00Z'. Precision
    (year-only vs full date) isn't distinguished yet -- deferred to
    enrichment, same as unit canonicalization."""
    if not value:
        return None
    return value.split("T")[0]


def dedup_facts_per_entity(facts, canonical_unit):
    """Keep exactly one fact per entity for this property. fetch_claims
    returns every dated statement (see its docstring for why the narrowing
    isn't done server-side), so this does the actual "most recent wins"
    comparison. Preference order: newer date beats older date, any date
    beats no date (a specific date suggests a deliberate record), then
    among ties -- e.g. Everest's elevation, recorded by multiple sources
    over decades with no date on any of them -- a match on the property's
    canonical unit if one is configured, then whichever came first."""
    best = {}
    for fact in facts:
        entity_qid = fact.extra["entity_qid"]
        current = best.get(entity_qid)
        if current is None:
            best[entity_qid] = fact
            continue

        fact_better = False
        if fact.published_at and current.published_at:
            if fact.published_at > current.published_at:
                fact_better = True
            elif fact.published_at == current.published_at:
                if canonical_unit and fact.extra["unit_qid"] == canonical_unit and current.extra["unit_qid"] != canonical_unit:
                    fact_better = True
        elif bool(fact.published_at) and not bool(current.published_at):
            fact_better = True
        elif not fact.published_at and not current.published_at:
            if canonical_unit and fact.extra["unit_qid"] == canonical_unit and current.extra["unit_qid"] != canonical_unit:
                fact_better = True

        if fact_better:
            best[entity_qid] = fact

    return list(best.values())


def ingest_property(pid, label, dimension, entity_class, canonical_unit, limit_per_property, retrieved_at):
    item_qids = fetch_item_ids(pid, limit_per_property, entity_class, canonical_unit)
    if entity_class and canonical_unit:
        mode = f"top by magnitude, class={entity_class}, unit={canonical_unit}"
    elif entity_class:
        mode = f"top by magnitude, class={entity_class}"
    else:
        mode = "unscoped/unsorted"
    print(f"  {pid} ({label}): {len(item_qids)} items to check ({mode})", file=sys.stderr)

    facts = []
    for i in range(0, len(item_qids), BATCH_SIZE):
        batch = item_qids[i:i + BATCH_SIZE]
        rows = fetch_claims(pid, batch)

        for row in rows:
            entity_qid = row["item"]["value"].rsplit("/", 1)[-1]
            entity_label = row.get("itemLabel", {}).get("value", entity_qid)
            stmt_id = row["stmt"]["value"].rsplit("/", 1)[-1]
            amount = row["amount"]["value"]
            unit_qid = row["unit"]["value"].rsplit("/", 1)[-1]
            unit_label = row.get("unitLabel", {}).get("value", unit_qid)
            point_in_time = format_point_in_time(row.get("pointInTime", {}).get("value"))

            unit_display = "" if unit_qid == "Q199" else f" {unit_label}"
            facts.append(RawFact(
                source="wikidata",
                source_item_id=stmt_id,
                retrieved_at=retrieved_at,
                published_at=point_in_time,
                title=entity_label,
                url=f"https://www.wikidata.org/wiki/{entity_qid}",
                section=None,
                raw_value=amount,
                raw_context=f"{entity_label} — {label}: {amount}{unit_display}",
                extra={
                    "property_id": pid,
                    "property_label": label,
                    "dimension": dimension,
                    "entity_qid": entity_qid,
                    "unit_qid": unit_qid,
                    "unit_label": unit_label,
                },
            ))

        if i + BATCH_SIZE < len(item_qids):
            polite_sleep(2.5)

    return dedup_facts_per_entity(facts, canonical_unit)


def run_cli(properties, default_out, description="Ingest quantity facts from Wikidata's SPARQL endpoint."):
    """Entry point for a theme script: pass its PROPERTIES dict and default
    output path. Usage (same across every theme script):
        python wikidata_<theme>.py                          # all configured properties
        python wikidata_<theme>.py --properties P1082,P2067  # just these
        python wikidata_<theme>.py --limit-per-property 500  # cap items per property
        python wikidata_<theme>.py --out data/raw/custom.jsonl
    """
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--properties", help="Comma-separated property IDs to ingest (default: all configured)")
    ap.add_argument("--limit-per-property", type=int, default=200,
                     help="Cap on items fetched per property (default: 200, for fast test runs)")
    ap.add_argument("--out", default=str(default_out), help="Output JSONL path")
    args = ap.parse_args()

    pids = args.properties.split(",") if args.properties else list(properties.keys())
    unknown = [p for p in pids if p not in properties]
    if unknown:
        ap.error(f"Unknown property id(s): {', '.join(unknown)}")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    out_path = Path(args.out)
    failed = []

    for idx, pid in enumerate(pids, start=1):
        label, dimension, entity_class, canonical_unit = properties[pid]
        print(f"[{idx}/{len(pids)}] {pid} ({label})", file=sys.stderr)
        try:
            facts = ingest_property(pid, label, dimension, entity_class, canonical_unit,
                                     args.limit_per_property, retrieved_at)
            written = write_raw_facts(facts, out_path)
            print(f"    -> {len(facts)} facts fetched, {written} new rows written", file=sys.stderr)
        except Exception as e:
            # A persistent failure on one property (e.g. a 502 that outlasts
            # every retry) shouldn't lose progress on the others -- log it
            # and keep going. Whatever that property already wrote via
            # write_raw_facts in earlier batches is preserved either way.
            print(f"    -> FAILED, skipping: {e}", file=sys.stderr)
            failed.append(pid)

        if idx < len(pids):
            polite_sleep(3.5)

    if failed:
        print(f"Done with failures. Output: {out_path}", file=sys.stderr)
        print(f"Failed properties (retry these individually): {','.join(failed)}", file=sys.stderr)
    else:
        print(f"Done. Output: {out_path}", file=sys.stderr)
