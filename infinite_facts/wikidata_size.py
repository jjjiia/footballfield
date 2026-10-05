#!/usr/bin/env python3
"""
Wikidata ingestion -- "size/dimensions" theme
------------------------------------------------
See wikidata_common.py for the shared query/retry/dedup engine and design
notes. This file just defines the property config for this theme.

Started as an "area" theme, but area alone turned out to have only 4
genuine candidate properties in all of Wikidata's 695 quantity-typed
properties (area, watershed area, water area, wing area) -- verified by
keyword-scanning labels/descriptions, not guessed. Broadened to cover
length/distance, area, and volume together as one "physical size" theme.

Two properties from the initial area-only search were dropped outright:
thickness and diameter, since their best real-data classes (paintings,
coins) are inherently small-number measurements -- a poor fit for a
"big/infinite facts" project regardless of scoping. water_area was also
dropped: its real usage is almost entirely narrow US municipal geography
(same trap as fiscal/tax revenue in the people theme -- verified thin/
absent at a broader scope, not just assumed).

Distance-dimension properties each pin a canonical_unit, but *not* a
single blanket one: the people theme's elevation/height already proved
real data mixes feet and metres in a way that silently breaks a plain
magnitude sort (a 14,203-foot Colorado peak outranking 8,849-metre
Everest). The first pass here pinned metre everywhere as a preemptive fix
-- but checking each property's actual unit distribution (not assuming)
found that was wrong for 5 of the 12 distance properties: length (river),
perimeter (lake), topographic isolation (mountain), and coastline
(country) are all overwhelmingly recorded in kilometre, not metre, at
these geographic scales (e.g. Canada's coastline is ~200,000 km); wheelbase
(car model) is overwhelmingly millimetre, not metre, since car specs are
conventionally quoted in mm. Pinning the wrong unit doesn't just skew
results -- it zeroes them out entirely (coastline scoped to metre returned
0 countries, since none record it that way).

Area and volume properties needed the same treatment: country-scale area
and river watershed area are recorded in square kilometre (not square
metre), aircraft wing area in square metre, lake volume in cubic metre,
and engine displacement in cubic centimetre -- each checked against real
data, not assumed. Ship gross/net tonnage are the exception: Wikidata's
own property description calls them a "unitless index," not a real
physical volume, so no unit pin applies there.
"""

from pathlib import Path

from wikidata_common import run_cli

DEFAULT_OUT = Path(__file__).parent / "data" / "raw" / "wikidata_size.jsonl"

METRE = "Q11573"
KILOMETRE = "Q828224"
MILLIMETRE = "Q174789"
SQUARE_KM = "Q712226"
SQUARE_METRE = "Q25343"
CUBIC_METRE = "Q25517"
CUBIC_CM = "Q1022113"

# property_id -> (label, dimension, entity_class_qid, canonical_unit_qid)
PROPERTIES = {
    # length/distance
    "P2044": ("elevation above sea level", "distance", "Q8502", METRE),   # mountain
    "P2048": ("height", "distance", "Q41176", METRE),                    # building
    "P2049": ("width", "distance", "Q11446", METRE),                     # ship
    "P2043": ("length", "distance", "Q4022", KILOMETRE),                 # river
    "P2547": ("perimeter", "distance", "Q23397", KILOMETRE),             # lake
    "P2660": ("topographic prominence", "distance", "Q8502", METRE),     # mountain
    "P2659": ("topographic isolation", "distance", "Q8502", KILOMETRE),  # mountain
    "P2261": ("beam", "distance", "Q11446", METRE),                      # ship
    "P3039": ("wheelbase", "distance", "Q3231690", MILLIMETRE),          # car model
    "P2787": ("longest span", "distance", "Q537127", METRE),             # road bridge
    "P5141": ("coastline", "distance", "Q6256", KILOMETRE),              # country
    "P2254": ("maximum operating altitude", "distance", "Q15056993", METRE),  # aircraft family

    # area
    "P2046": ("area", "area", "Q6256", SQUARE_KM),                       # country
    "P2053": ("watershed area", "area", "Q4022", SQUARE_KM),             # river
    "P2112": ("wing area", "area", "Q15056995", SQUARE_METRE),           # aircraft model

    # volume
    "P2234": ("volume as quantity", "volume", "Q23397", CUBIC_METRE),    # lake
    "P1093": ("gross tonnage", "volume", "Q11446", None),                # ship (Wikidata's own description: "unitless index," not a real unit to mix)
    "P2790": ("net tonnage", "volume", "Q11446", None),                  # ship (same: unitless index)
    "P8628": ("engine displacement", "volume", "Q15057021", CUBIC_CM),   # engine model
}

if __name__ == "__main__":
    run_cli(PROPERTIES, DEFAULT_OUT, description="Ingest 'size/dimensions' facts from Wikidata.")
