# Infinite Context Facts Page — Project Plan

A page that presents a fact, then chains to comparable facts indefinitely
(same cost, same count, same place, same era, etc.) — in the spirit of
neal.fun's "Size of Space" / "What Are The Odds?"

This plan is broken into phases. **Work through them in order, one at a
time, in separate Claude Code sessions or clearly separated turns.** For
each phase, paste the prompt as-is. Every prompt explicitly asks Claude
Code to propose a plan first and wait for approval before writing code —
don't skip that step, even when a phase looks simple.

---

## Phase 0 — Project setup

**Goal:** get a repo scaffold in place before any real logic exists.

**Prompt:**
```
I'm starting a new project: a web page that shows a fact, then chains to
comparable facts indefinitely (similar to neal.fun's "Size of Space" or
"What Are The Odds?" pages). Example chain: "$12.5 billion" -> "roughly
[Company]'s market cap" -> "which is about the GDP of [Country]" -> ...

Before writing any code, propose:
1. A repo folder structure for this project (data ingestion, enrichment,
   storage, traversal logic, frontend — as separate concerns)
2. What language/stack you'd recommend for each part, with brief reasoning
   (I have no strong preference yet — optimize for something you can
   iterate on quickly and that I can also run locally without much setup)
3. A short README outline describing the project

Do not write implementation code yet. Just the structure, stack choice,
and README outline. I'll confirm before we proceed to Phase 1.
```

---

## Phase 1 — Data ingestion (raw facts in) — DONE

**Goal:** get raw facts from source material into a consistent raw format.

**Status:** implemented, using Wikidata (not Numlock News — dropped as a
source; structured data with units already attached is a better fit than
extracting bolded numbers from newsletter prose). Lives in `infinite_facts/`:

- `base.py` — the source-agnostic `RawFact` schema (source, source_item_id,
  retrieved_at, published_at, title, url, section, raw_value, raw_context,
  extra) and a JSONL writer that dedups by `source_item_id`.
- `wikidata_ingest.py` — queries `query.wikidata.org`'s SPARQL endpoint
  directly for a curated list of properties (see `PROPERTIES` in that file),
  rather than downloading the full ~30GB dump — the property list is small
  enough that live paginated queries are simpler to iterate on. Key design
  points, all learned by hitting real problems against real data:
  - Items are scoped to a relevant "instance of" class (e.g. country,
    mountain) before sorting by magnitude, both because an unscoped sort
    times out on the public endpoint for high-volume properties, and
    because an unscoped/unsorted fetch surfaces obscure, low-magnitude
    entities (empty islands, alpine huts) rather than recognizable ones.
  - Some properties additionally pin one canonical unit within that join
    (e.g. metres for elevation) — a bare magnitude sort silently breaks
    when a property mixes units (a 14,203-foot Colorado peak numerically
    outranking 8,849-metre Everest).
  - Units are stored as-is per fact (`unit_qid` + `unit_label`), not
    converted to a canonical unit at ingestion time — real data showed
    properties mixing units in ways that make a fixed per-property
    assumption wrong (mass in both kg and Jupiter masses, etc.).
    Canonicalization is deferred to enrichment (Phase 2), via each unit's
    own `P2370` "conversion to SI unit" factor.
  - When an item has multiple statements for the same property with no
    unique preferred rank (common — e.g. population recorded in several
    different years, or the same mountain's elevation logged by multiple
    editors), the most-recently-dated one is kept; where none are dated,
    one is picked deterministically (preferring the canonical unit) rather
    than emitting duplicates.
  - 8 of the 18 configured properties don't yet have a verified "notable
    entity class" to scope by (mass, speed, volume, price, students,
    members, followers, deaths, injured, casualties) and currently fall
    back to an unscoped/unsorted fetch — fine for schema testing, not yet
    for picking "the biggest X." Follow-up work, not blocking Phase 2.

---

## Phase 2 — Fact classification & enrichment

**Goal:** turn each raw fact ("$12.5 billion annually") into a structured
node with the fields needed to compare it against other facts.

**Prompt:**
```
Now I need an enrichment step that takes a raw fact (raw text + context
sentence) and produces a structured record with:

- value: the numeric value, extracted
- unit: the stated unit (USD, people, meters, percent, etc.)
- dimension: a normalized category — currency | count | mass | distance
  | time | energy | area | volume | rate | percentage
- normalized_value: the value converted to a canonical unit per dimension
  (e.g. all currency -> USD, all mass -> kg, all distance -> meters)
- per: a rate qualifier if applicable (e.g. "year", "day"), else null
- time_scope: a short human-readable description of when this fact applies
  (e.g. "year-to-date 2026", "opening weekend", "forward-looking
  projection to 2100") — infer this from the context sentence
- entities: notable named entities mentioned (places, companies, people)
- topic_tags: 2-4 short topic tags

Before writing code, propose a plan for:
1. Whether this should be rule-based (regex/parsing libraries for units),
   LLM-based (a classification prompt), or a hybrid — with reasoning on
   where each approach is more reliable
2. What library/approach to use for real unit conversion (don't hand-roll
   unit math if a solid library exists for the target language)
3. How to handle ambiguous or unparseable facts (e.g. "a million shy of"
   — no explicit unit) — should these be dropped, flagged, or stored with
   partial data?
4. The exact schema (field names, types) for the enriched fact record

Wait for my approval on the plan before implementing. Once approved, run
it against a small sample (10-20 facts) first so we can review output
quality before running it on the full dataset.
```

---

## Phase 3 — Storage & comparison edges

**Goal:** persist enriched facts and compute the "comparable to" relationships
between them.

**Prompt:**
```
Now I need to store enriched facts and generate comparison edges between
them. Edge types:

- magnitude_match: same dimension, normalized_value within roughly 0.5x-2x
  of each other
- unit_conversion: same dimension, different unit, exact converted value
- cost_equivalence: both dimension=currency, any magnitude, framed as
  "costs about the same as"
- count_equivalence: both dimension=count, similar magnitude
- rate_equivalence: both have a non-null "per" field, normalized to the
  same time unit
- shared_entity: overlapping "entities" values
- shared_time: same or adjacent time_scope
- thematic: overlapping topic_tags

Before writing code, propose a plan for:
1. Storage choice — SQLite is probably right for a project this size,
   but tell me if you'd recommend otherwise, with reasoning
2. Schema for the facts table and a separate edges table (or a graph
   database, if you think that's actually warranted at this scale —
   probably not, but make the case either way)
3. Whether edges should be precomputed and stored, or computed on-demand
   at query time — tradeoffs of each
4. How we avoid a fact only ever connecting to near-duplicates (e.g. two
   facts from the same article) — some kind of diversity constraint

Wait for approval before implementing.
```

---

## Phase 4 — Reference quantity library (the "never run out" fallback)

**Goal:** a library of well-known quantities (Olympic pool volume, average
car weight, US federal budget, Earth's circumference, etc.) that lets the
chain always have a landing pad even when curated facts run thin at a
given magnitude.

**Prompt:**
```
I want a fallback library of ~100-200 well-known reference quantities
(e.g. "an Olympic swimming pool holds ~2,500,000 liters", "an average
car weighs ~1,500 kg", "the US federal budget is ~$6.75 trillion") so
the traversal engine always has something to compare to, even when
curated facts run out at a given magnitude/dimension.

Before writing code, propose a plan for:
1. How to source this list responsibly — favor well-established,
   slow-changing reference figures over anything that needs frequent
   updating, and flag anything that should cite a source
2. The data format (should match the enriched fact schema from Phase 2
   so it can plug into the same comparison logic)
3. Which dimensions currently have the thinnest coverage from our real
   ingested facts, so we prioritize filling those first

Wait for approval before implementing.
```

---

## Phase 5 — Traversal engine

**Goal:** given a current fact, select the next fact to show.

**Prompt:**
```
Now build the traversal engine: given a current fact, select the next
fact to display in the chain.

Before writing code, propose a plan for:
1. The selection algorithm — e.g. alternate between a magnitude-jump and
   a theme/entity-jump so the chain doesn't stay in one topic forever,
   with some randomness so repeated visits don't produce identical chains
2. How to avoid loops (returning to a fact already shown in this session)
3. How to blend curated facts with the reference-quantity fallback from
   Phase 4 when curated options are thin
4. What the function signature/API should look like (I'll need to call
   this from the frontend)

Wait for approval before implementing. Once built, test it by generating
and printing out 3-4 sample chains of ~10 facts each so we can sanity
check the pacing and variety before touching the frontend.
```

---

## Phase 6 — Frontend

**Goal:** a page that displays the chain, one fact at a time, loading more
as the user scrolls or clicks.

**Prompt:**
```
Now build the frontend: a page showing one fact at a time, with a way to
move to the next fact in the chain (infinite scroll or a "next" action —
tell me which you'd recommend for this content and why).

Before writing code, propose a plan for:
1. Frontend approach given the stack we chose in Phase 0
2. Layout for a single fact "card" — what's shown (the value, the
   context sentence, the source, maybe the comparison type/relationship
   to the previous fact)
3. How the frontend calls the traversal engine from Phase 5 (API route,
   direct function call, etc. depending on stack)
4. Loading/pacing — should facts appear instantly or with a small reveal
   animation to invite lingering on each one (like neal.fun's style)

Wait for approval before implementing.
```

---

## Phase 7 — Expansion & polish (later)

Once the above is working end-to-end with the Wikidata data source:
- Add more ingestion sources (other structured datasets, government
  statistical releases, etc.) — Phase 1's source-agnostic storage format
  should make this additive rather than a rewrite
- Add a scheduled job to re-run ingestion for fresh Wikidata values
- Add basic analytics on which chains/facts get the most engagement, to
  inform future curation
- Consider letting users "pin" or share a specific chain

---

## Working notes

- **Always make Claude Code show you the plan before writing code** —
  every prompt above ends with "wait for approval." Don't paste all
  phases into one session at once; work through them one at a time so
  each plan can actually be reviewed against working code from the
  previous phase.
- **Test on small samples first** (Phases 2 and 5 call this out
  explicitly) — enrichment quality and chain variety are both things
  you want to eyeball before running against the full dataset.
