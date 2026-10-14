"""Build populations/wikidata/people_counts.json for nested_people.html.

The counts are the Wikidata people counts the old people page used (embedded
as DATA in "not in use/people.html", built from
infinite_facts/data/raw/wikidata_people.jsonl). Every value is a number of people.

Left out:
- vaccinations (doses) and viewers (views): not counts of people
- visitors/passengers under 1,000 a year: wrong in Wikidata (e.g. an airport
  with 398 passengers a year)
- items with no English name (the old page showed their ID, e.g. "Q36159")

Usage: python populations/wikidata/build_people_counts.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")

text = open(os.path.join(ROOT, "not in use", "people.html")).read()
start = text.index("const DATA = ") + len("const DATA = ")
data, _ = json.JSONDecoder().raw_decode(text[start:])

# category key in the old page -> section name on the new page
SECTIONS = [
    ("population", "Country populations"),
    ("languages", "Language speakers"),
    ("followers", "Social media followers"),
    ("visitors", "Visitors and passengers per year"),
    ("venues", "Venue capacity"),
    ("other", "Other"),
]
data["other"] = data["subscribers"] + data["deaths"] + data["registered_users"]

out = []
for key, section in SECTIONS:
    items = [d for d in data[key]
             if not (key == "visitors" and d["v"] < 1000) and not re.fullmatch(r"Q\d+", d["t"])]
    items.sort(key=lambda d: -d["v"])
    out.append({
        "key": key,
        "section": section,
        "items": [{"q": d["q"], "name": d["t"], "count": round(d["v"]), "property": d["p"]} for d in items],
    })
    print(f"{section}: {len(items)}")

with open(os.path.join(HERE, "people_counts.json"), "w") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
