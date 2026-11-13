#!/usr/bin/env python3
"""给内置快照补齐结构化版权字段；不改正文和证据。

未声明可复用许可的来源明确记录为 ``not-declared``，只允许短引用分发，
不能据此宣称获得转载授权。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main() -> int:
    prompt_path = DATA / "prompts.json"
    payload = json.loads(prompt_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for item in payload["items"]:
        source = dict(item.get("source") or {})
        source["license"] = source.get("license") or "not-declared"
        source["rights_basis"] = (
            source.get("rights_basis") or "short-quotation-with-attribution"
        )
        source["redistribution"] = source.get("redistribution") or "excerpt-only"
        item["source"] = source
        counts[source["rights_basis"]] = counts.get(source["rights_basis"], 0) + 1

    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    prompt_path.write_text(body, encoding="utf-8")

    meta_path = DATA / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    meta["require_rights"] = True
    meta["rights"] = counts
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "ok": True,
        "count": len(payload["items"]),
        "rights": counts,
        "sha256": meta["sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
