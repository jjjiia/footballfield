#!/usr/bin/env python3
"""Rebuild viz/size_data.json from data/raw/wikidata_size_{distance,area,volume}.jsonl."""
import json
import collections
from pathlib import Path

ROOT = Path(__file__).parent.parent

payload = {}
for dim in ["distance", "area", "volume"]:
    rows = [json.loads(l) for l in open(ROOT / "data" / "raw" / f"wikidata_size_{dim}.jsonl")]
    by_prop = collections.defaultdict(list)
    for r in rows:
        try:
            v = float(r["raw_value"])
        except ValueError:
            continue
        if v <= 0:
            continue
        by_prop[r["extra"]["property_label"]].append({
            "t": r["title"],
            "v": v,
            "u": r["extra"]["unit_label"],
            "q": r["extra"]["entity_qid"],
        })
    props = []
    for label, items in by_prop.items():
        unit_counts = collections.Counter(i["u"] for i in items)
        dominant = unit_counts.most_common(1)[0][0]
        props.append({"label": label, "dominant_unit": dominant, "items": items})
    payload[dim] = props

out_path = Path(__file__).parent / "size_data.json"
with open(out_path, "w") as f:
    json.dump(payload, f)
print(f"{out_path}: {out_path.stat().st_size:,} bytes")
