#!/usr/bin/env python3
"""把旧来源索引升级为带 SHA-256 和抓取元数据的快照 manifest。"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "reports" / "sources"
INDEX = SOURCES / "index.json"

MEDIA_TYPES = {
    ".html": "text/html",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
}


def main() -> int:
    raw = json.loads(INDEX.read_text(encoding="utf-8"))
    legacy = raw.get("sources", raw)
    rows = {}
    for url, entry in legacy.items():
        item = dict(entry)
        name = item.get("file")
        if not name:
            rows[url] = item
            continue
        path = SOURCES / name
        if not path.exists():
            item["ok"] = False
            item["error"] = "snapshot file missing"
            rows[url] = item
            continue
        data = path.read_bytes()
        item.update({
            "file": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
            "media_type": MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream"),
            "fetched_at": item.get("fetched_at")
            or datetime.fromtimestamp(
                path.stat().st_mtime,
                tz=timezone(timedelta(hours=8)),
            ).isoformat(timespec="seconds"),
            "ok": True,
        })
        item.pop("error", None)
        rows[url] = item

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(
            timespec="seconds"
        ),
        "sources": rows,
    }
    INDEX.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(INDEX),
        "sources": len(rows),
        "snapshotted": sum(1 for row in rows.values() if row.get("sha256")),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
