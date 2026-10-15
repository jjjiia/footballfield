"""Build populations/wikidata/people_counts.json for nested_people.html.

The counts are the Wikidata people counts the old people page used (embedded
as DATA in "not in use/people.html", built from
infinite_facts/data/raw/wikidata_people.jsonl). Every value is a number of people.

Left out:
- vaccinations (doses) and viewers (views): not counts of people
- visitors/passengers under 1,000 a year: wrong in Wikidata (e.g. an airport
  with 398 passengers a year)
- items with no English name (the old page showed their ID, e.g. "Q36159")

Followers are Instagram followers, fetched from Wikidata for the people the old
page listed: each person's social media followers (P8687) statements with an
Instagram username (P2003) qualifier, the latest by point in time (P585).
People with no Instagram count in Wikidata are left out.

Usage: python populations/wikidata/build_people_counts.py
"""
import json
import os
import re
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")

text = open(os.path.join(ROOT, "not in use", "people.html")).read()
start = text.index("const DATA = ") + len("const DATA = ")
data, _ = json.JSONDecoder().raw_decode(text[start:])

# category key in the old page -> section name on the new page
SECTIONS = [
    ("population", "Country populations"),
    ("languages", "Language speakers"),
    ("followers", "Instagram followers"),
    ("visitors", "Visitors and passengers per year"),
    ("venues", "Venue capacity"),
    ("other", "Other"),
]
data["other"] = data["subscribers"] + data["deaths"] + data["registered_users"]


def instagram_followers(qids):
    """{qid: latest Instagram follower count} from Wikidata, for those that have one."""
    out = {}
    for i in range(0, len(qids), 50):
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": "claims", "format": "json"})
        req = urllib.request.Request(url, headers={"User-Agent": "footballfield-people-counts/0.1"})
        entities = json.load(urllib.request.urlopen(req))["entities"]
        for q, e in entities.items():
            best = None
            for c in e.get("claims", {}).get("P8687", []):
                quals = c.get("qualifiers", {})
                if c["rank"] == "deprecated" or "P2003" not in quals:
                    continue
                when = quals["P585"][0]["datavalue"]["value"]["time"] if "P585" in quals else ""
                n = float(c["mainsnak"]["datavalue"]["value"]["amount"])
                if best is None or when > best[0]:
                    best = (when, n)
            if best:
                out[q] = best[1]
    return out


ig = instagram_followers([d["q"] for d in data["followers"]])
print(f"Instagram followers: {len(ig)} of {len(data['followers'])} people")
data["followers"] = [{**d, "v": ig[d["q"]], "p": "Instagram followers"} for d in data["followers"] if d["q"] in ig]

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
