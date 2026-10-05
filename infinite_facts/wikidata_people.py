#!/usr/bin/env python3
"""
Wikidata ingestion -- "count of people" theme
-----------------------------------------------
See wikidata_common.py for the shared query/retry/dedup engine and design
notes. This file just defines the property config for this theme.

Reoriented around a single coherent theme: raw counts of people. Wikidata
has no dedicated "person" quantity unit for plain headcounts (checked --
the only "person"-related units are composite/rate units like person-year
or person per square km); headcounts are just dimensionless numbers, same
as population. This replaced an earlier, much broader 87-property spread
across many unrelated dimensions (mass, price, GDP, film budgets, etc.),
which is why every entry below is dimension="count".
"""

from pathlib import Path

from wikidata_common import run_cli

DEFAULT_OUT = Path(__file__).parent / "data" / "raw" / "wikidata_people.jsonl"

# property_id -> (label, dimension, entity_class_qid, canonical_unit_qid)
#
# entity_class_qid scopes the item lookup to a specific "instance of" class
# (e.g. country, mountain) before sorting by magnitude. This matters: sorting
# by magnitude across a property's *entire* range times out on the public
# endpoint for high-volume properties (a full scan+sort over millions of
# rows), and an unscoped/unsorted lookup surfaces whatever Wikidata returns
# first, which skews toward obscure, low-magnitude entities rather than
# recognizable ones. Scoping to a class keeps the candidate set small enough
# to sort quickly *and* keeps results relevant.
#
# canonical_unit_qid additionally constrains to one specific unit within the
# scoped class, for dimensions real data showed mixing units in a way that
# breaks a plain numeric sort. None elsewhere means "not checked yet," not
# "confirmed fine" -- though for this theme every property is dimensionless
# by nature, so no canonical_unit was needed.
PROPERTIES = {
    # demographics
    "P1082": ("population", "count", "Q6256", None),                    # country
    "P1540": ("male population", "count", "Q6256", None),               # country
    "P1539": ("female population", "count", "Q6256", None),             # country
    "P6498": ("illiterate population", "count", "Q6256", None),         # country (thin: 1 result in testing, but good quality)
    "P2573": ("number of out-of-school children", "count", "Q6256", None),  # country
    "P12712": ("population by native language", "count", "Q659103", None),  # commune of Romania (narrow, but that's the real data)

    # about a person themselves
    "P8687": ("social media followers", "count", "Q5", None),           # human
    "P1971": ("number of children", "count", "Q5", None),               # human
    "P1345": ("number of victims of killer", "count", "Q5", None),      # human
    "P5436": ("number of viewers/listeners", "count", "Q5", None),      # human (fragmented across classes; this is the top one)

    # organizations
    "P1128": ("employees", "count", "Q4830453", None),                  # business
    "P3744": ("number of subscribers", "count", "Q4830453", None),      # business
    "P2124": ("member count", "count", "Q43229", None),                 # organization
    "P6125": ("number of volunteers", "count", "Q43229", None),         # organization
    "P4909": ("number of players in region", "count", "Q43229", None),  # organization
    "P2196": ("count of students", "count", "Q2385804", None),          # educational institution
    "P1833": ("number of registered users/contributors", "count", "Q72705885", None),  # Mastodon instance (narrow)

    # elections
    "P1831": ("electorate", "count", "Q40231", None),                   # election
    "P1697": ("total valid votes", "count", "Q40231", None),            # election
    "P1868": ("ballots cast", "count", "Q40231", None),                 # election
    "P5044": ("number of spoilt votes", "count", "Q40231", None),       # election
    "P5045": ("number of blank votes", "count", "Q40231", None),        # election
    "P1867": ("eligible voters", "count", "Q40231", None),              # election
    "P8682": ("number of negative votes", "count", "Q43109", None),     # referendum
    "P8683": ("number of support votes", "count", "Q43109", None),      # referendum
    "P1342": ("number of seats", "count", "Q1752346", None),            # assembly

    # disasters/accidents
    "P1120": ("number of deaths", "count", "Q3241045", None),           # disease outbreak
    "P9107": ("number of vaccinations", "count", "Q3241045", None),     # disease outbreak
    "P1339": ("number of injured", "count", "Q1078765", None),          # railway accident
    "P1590": ("number of casualties", "count", "Q1078765", None),       # railway accident
    "P1561": ("number of survivors", "count", "Q744913", None),         # aviation accident
    "P1446": ("number of missing", "count", "Q3030513", None),          # disappearance
    "P9924": ("number of evacuated", "count", "Q169950", None),         # wildfire

    # venues
    "P1083": ("maximum capacity", "count", "Q483110", None),            # stadium
    "P1174": ("visitors per year", "count", "Q33506", None),            # museum
    "P3872": ("patronage", "count", "Q1248784", None),                  # airport

    # other
    "P1098": ("number of speakers, writers, or signers", "count", "Q34770", None),  # language
    "P8876": ("number of taxpayers", "count", "Q8161", None),           # tax (odd fit: attaches to the tax concept, not a country)
    "P9740": ("number of request signatories", "count", "Q46337", None),  # manifesto
    "P13564": ("third-gender population", "count", "Q620471", None),    # upazila of Bangladesh (near-zero usage: 5 total)
    "P9077": ("number of aid beneficiaries", "count", "Q1968122", None),  # National Red Cross and Red Crescent society (near-zero usage: 3 total)

    # NOTE: even after filtering the known 99999999 placeholder, top-end
    # values still look unreliable (e.g. a "Thanksgiving Messaging Campaign"
    # with 20,000,000 participants) -- needs manual spot-checking before
    # trusting this property's magnitude-sorted results.
    "P1132": ("number of participants", "count", "Q30612", None),       # clinical trial
}

if __name__ == "__main__":
    run_cli(PROPERTIES, DEFAULT_OUT, description="Ingest 'count of people' facts from Wikidata.")
