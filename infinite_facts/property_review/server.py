#!/usr/bin/env python3
"""
Local property-review tool
---------------------------
Serves a page that cycles through the candidate Wikidata quantity
properties (../../wikidata_quantity_properties.json) one at a time, so they
can be hand-picked rather than guessed at: 'y' keeps a property, 'n'
discards it, 'u' marks it unsure (reviewed separately later), 'z' undoes
the last decision. Decisions persist to disk after every keypress, so
closing the browser mid-review loses nothing.

Reviewed in descending usage_count order (highest-impact properties first).

Output:
    wikidata_quantity_properties_review_state.json  -- every decision made
        so far (for resuming) plus the decision order (for undo)
    wikidata_quantity_properties_selected.json       -- just the "y" ones,
        rewritten after every decision
    wikidata_quantity_properties_unsure.json         -- just the "u" ones,
        rewritten after every decision

Usage:
    python server.py [--port 8765]
    Then open http://localhost:8765/ in a browser.
"""
import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # footballfield/
SOURCE_PATH = ROOT / "wikidata_quantity_properties.json"
STATE_PATH = ROOT / "wikidata_quantity_properties_review_state.json"
SELECTED_PATH = ROOT / "wikidata_quantity_properties_selected.json"
UNSURE_PATH = ROOT / "wikidata_quantity_properties_unsure.json"
HTML_PATH = Path(__file__).resolve().parent / "index.html"


def load_items():
    with SOURCE_PATH.open() as f:
        data = json.load(f)
    items = [{"id": pid, **info} for pid, info in data.items()]
    items.sort(key=lambda x: -(x.get("usage_count") or 0))
    return items


def load_state():
    if STATE_PATH.exists():
        with STATE_PATH.open() as f:
            return json.load(f)
    return {"decisions": {}, "order": []}


def save_state(state):
    with STATE_PATH.open("w") as f:
        json.dump(state, f, indent=2)


def save_selected(items_by_id, state):
    selected = {
        pid: items_by_id[pid]
        for pid, decision in state["decisions"].items()
        if decision == "y" and pid in items_by_id
    }
    with SELECTED_PATH.open("w") as f:
        json.dump(selected, f, indent=2)


def save_unsure(items_by_id, state):
    unsure = {
        pid: items_by_id[pid]
        for pid, decision in state["decisions"].items()
        if decision == "u" and pid in items_by_id
    }
    with UNSURE_PATH.open("w") as f:
        json.dump(unsure, f, indent=2)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            html = HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif self.path == "/api/items":
            items = load_items()
            state = load_state()
            self._send_json({"items": items, "state": state})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        items = load_items()
        items_by_id = {i["id"]: i for i in items}
        state = load_state()

        if self.path == "/api/decision":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            pid = body["id"]
            decision = body["decision"]  # "y", "n", or "u"

            if pid in state["decisions"]:
                state["order"].remove(pid)
            state["decisions"][pid] = decision
            state["order"].append(pid)

            save_state(state)
            save_selected(items_by_id, state)
            save_unsure(items_by_id, state)
            self._send_json({
                "ok": True,
                "kept_count": sum(1 for v in state["decisions"].values() if v == "y"),
                "unsure_count": sum(1 for v in state["decisions"].values() if v == "u"),
            })

        elif self.path == "/api/undo":
            if state["order"]:
                last_id = state["order"].pop()
                del state["decisions"][last_id]
                save_state(state)
                save_selected(items_by_id, state)
                save_unsure(items_by_id, state)
                self._send_json({"ok": True, "undone_id": last_id})
            else:
                self._send_json({"ok": False, "error": "nothing to undo"}, status=400)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # keep console quiet


def main():
    ap = argparse.ArgumentParser(description="Local Wikidata property review tool.")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    if not SOURCE_PATH.exists():
        print(f"Source file not found: {SOURCE_PATH}", file=sys.stderr)
        sys.exit(1)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Serving at http://127.0.0.1:{args.port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
