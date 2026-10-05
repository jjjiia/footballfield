"""Build the data payload for the people.html number-line scrolly.

Categories, in the order they're introduced by the scroll steps:
  population   (P1082, all countries)               -- red
  languages    (P1098, number of speakers/writers/signers) -- teal
  followers    (P8687, social media followers)       -- blue
  visitors     (P1174 visitors per year, P3872 patronage)  -- green
  venues       (P1083 maximum capacity)              -- purple

All five categories fit inside the same linear domain once it's been widened
to fit every country's population (the biggest category), so the axis only
needs to zoom out twice: once to fit Mexico/Canada next to the US, and once
more to fit all ~208 countries. Everything after that is added dots, not a
rescale.
"""
import json

VIZ_DIR = "."
DATA_FILE = "../data/raw/wikidata_people.jsonl"


def load_rows():
    return [json.loads(l) for l in open(DATA_FILE)]


def collect(rows, prop_ids, min_val=0):
    out = []
    for r in rows:
        if r["extra"]["property_id"] in prop_ids:
            try:
                v = float(r["raw_value"])
            except ValueError:
                continue
            if v < min_val:
                continue
            out.append({"v": v, "t": r["title"], "q": r["extra"]["entity_qid"], "p": r["extra"]["property_label"]})
    return out


def main():
    rows = load_rows()

    population = collect(rows, {"P1082"})
    languages = collect(rows, {"P1098"})
    followers = collect(rows, {"P8687"}, min_val=0.01)
    visitors = collect(rows, {"P1174", "P3872"})
    venues = collect(rows, {"P1083"})

    payload = {
        "population": population,
        "languages": languages,
        "followers": followers,
        "visitors": visitors,
        "venues": venues,
    }

    with open("people_numberline_data.json", "w") as f:
        json.dump(payload, f)

    for name, data in payload.items():
        vals = [d["v"] for d in data]
        print(f"{name}: {len(data)} rows, min {min(vals):,.0f}, max {max(vals):,.0f}")


if __name__ == "__main__":
    main()
