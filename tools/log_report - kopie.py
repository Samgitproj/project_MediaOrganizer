# [SECTION: IMPORTS]
from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List
# [END: SECTION: IMPORTS]

# [FUNC: def read_jsonl]
def read_jsonl(path: str | Path) -> Iterable[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                # sla corrupte regels over
                continue

# [END: FUNC: def read_jsonl]

# [FUNC: def filter_events]
def filter_events(
    events: Iterable[Dict[str, Any]], level: str | None = None, text: str | None = None
):
    for e in events:
        if level and e.get("level", "").upper() != level.upper():
            continue
        if text and text.lower() not in str(e.get("msg", "")).lower():
            continue
        yield e

# [END: FUNC: def filter_events]

# [FUNC: def summarize]
def summarize(events: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for e in events:
        lvl = e.get("level", "UNKNOWN")
        counts[lvl] = counts.get(lvl, 0) + 1
    return counts

# [END: FUNC: def summarize]

# [FUNC: def main]
def main(argv: List[str] | None = None) -> int:
    # simpele console-logging als er nog niets is geconfigureerd
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    log = logging.getLogger("tools.log_report")

    ap = argparse.ArgumentParser(description="JSONL log tools")
    ap.add_argument("--file", default="logs/log.jsonl", help="pad naar JSONL log")
    ap.add_argument("--summary", action="store_true", help="toon telling per level")
    ap.add_argument("--level", help="filter op level (INFO/DEBUG/...)")
    ap.add_argument("--grep", help="filter op tekst")
    ns = ap.parse_args(argv)

    ev_total = list(read_jsonl(ns.file))
    log.info("geladen: %d events uit %s", len(ev_total), ns.file)

    ev = ev_total
    if ns.level or ns.grep:
        ev = list(filter_events(ev_total, ns.level, ns.grep))
        log.info("na filter(level=%s, grep=%s): %d events", ns.level, ns.grep, len(ev))

    if ns.summary:
        s = summarize(ev)
        for k, v in sorted(s.items()):
            print(f"{k:8s} {v}")
        log.info("summary gereed (%d niveaus)", len(s))
        return 0

    for e in ev:
        print(
            f"{e.get('ts','?')} | {e.get('level','?'):7s} | {e.get('name','?'):20s} | {e.get('msg','')}"
        )
    log.info("print gereed (%d regels)", len(ev))
    return 0

# [END: FUNC: def main]

# [SECTION: MAIN]
if __name__ == "__main__":
    raise SystemExit(main())
# [END: SECTION: MAIN]

