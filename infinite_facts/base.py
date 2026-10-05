"""Source-agnostic schema for raw ingested facts, shared across ingestion
sources (Wikidata, future sources)."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class RawFact:
    source: str
    source_item_id: str
    retrieved_at: str
    published_at: Optional[str]
    title: str
    url: str
    section: Optional[str]
    raw_value: str
    raw_context: Optional[str]
    extra: dict = field(default_factory=dict)


def write_raw_facts(facts, out_path: Path) -> int:
    """Append facts to a JSONL file, skipping any whose source_item_id is
    already present so re-running ingestion doesn't duplicate rows."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seen = set()
    if out_path.exists():
        with out_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    seen.add(json.loads(line)["source_item_id"])

    written = 0
    with out_path.open("a", encoding="utf-8") as f:
        for fact in facts:
            if fact.source_item_id in seen:
                continue
            seen.add(fact.source_item_id)
            f.write(json.dumps(asdict(fact), ensure_ascii=False) + "\n")
            written += 1
    return written
