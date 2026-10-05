#!/usr/bin/env python3
"""Rebuild viz/people_data.json from data/raw/wikidata_people.jsonl, grouped
into the same thematic clusters used in wikidata_people.py's comments."""
import json
import collections
from pathlib import Path

ROOT = Path(__file__).parent.parent

CLUSTER_MAP = {
    "P1082": "demographics", "P1540": "demographics", "P1539": "demographics",
    "P6498": "demographics", "P2573": "demographics", "P12712": "demographics",
    "P8687": "person", "P1971": "person", "P1345": "person", "P5436": "person",
    "P1128": "organizations", "P3744": "organizations", "P2124": "organizations",
    "P6125": "organizations", "P4909": "organizations", "P2196": "organizations",
    "P1833": "organizations",
    "P1831": "elections", "P1697": "elections", "P1868": "elections",
    "P5044": "elections", "P5045": "elections", "P1867": "elections",
    "P8682": "elections", "P8683": "elections", "P1342": "elections",
    "P1120": "disasters", "P9107": "disasters", "P1339": "disasters",
    "P1590": "disasters", "P1561": "disasters", "P1446": "disasters",
    "P9924": "disasters",
    "P1083": "venues", "P1174": "venues", "P3872": "venues",
    "P1098": "other", "P8876": "other", "P9740": "other",
    "P13564": "other", "P9077": "other", "P1132": "other",
}

rows = [json.loads(l) for l in open(ROOT / "data" / "raw" / "wikidata_people.jsonl")]
by_cluster = collections.defaultdict(lambda: collections.defaultdict(list))
missing = set()
for r in rows:
    pid = r["extra"]["property_id"]
    cluster = CLUSTER_MAP.get(pid)
    if cluster is None:
        missing.add(pid)
        continue
    try:
        v = float(r["raw_value"])
    except ValueError:
        continue
    if v <= 0:
        continue
    by_cluster[cluster][r["extra"]["property_label"]].append({
        "t": r["title"],
        "v": v,
        "u": r["extra"]["unit_label"],
        "q": r["extra"]["entity_qid"],
    })

if missing:
    print("WARNING: unmapped property ids:", missing)

payload = {}
for cluster, props in by_cluster.items():
    plist = []
    for label, items in props.items():
        units = collections.Counter(i["u"] for i in items)
        dominant = units.most_common(1)[0][0]
        plist.append({"label": label, "dominant_unit": dominant, "items": items})
    payload[cluster] = plist

out_path = Path(__file__).parent / "people_data.json"
with open(out_path, "w") as f:
    json.dump(payload, f)
print(f"{out_path}: {out_path.stat().st_size:,} bytes")
