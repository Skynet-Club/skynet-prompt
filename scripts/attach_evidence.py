#!/usr/bin/env python3
"""把 source-check 报告冻结为条目内的结构化证据字段。

判定只使用已有报告和 nature，不推断报告中不存在的结论：
- ok + 本人原文 -> verbatim
- ok + 未核实 -> verbatim
- 他人整理 -> paraphrase
- 其余 missing -> unverified
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORT = ROOT / "reports" / "source-check.json"


def load_rows() -> list[dict]:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise SystemExit(f"source-check 报告 rows 不是数组：{REPORT}")
    return rows


def main() -> int:
    prompt_path = DATA / "prompts.json"
    meta_path = DATA / "meta.json"
    payload = json.loads(prompt_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in load_rows()}

    counts = {"verbatim": 0, "paraphrase": 0, "unverified": 0}
    for item in payload["items"]:
        row = rows.get(item["id"])
        if row is None:
            verdict = "unverified"
            method = None
        elif item.get("nature") == "他人整理":
            verdict = "paraphrase"
            method = row.get("via")
        elif row.get("verdict") == "ok":
            verdict = "verbatim"
            method = row.get("via")
        else:
            verdict = "unverified"
            method = row.get("via")
        counts[verdict] += 1
        item["source"] = {
            "quote": item["en"],
            "url": item["url"],
            "author": item["author"],
            "published_at": item["date"],
        }
        item["evidence"] = {
            "verdict": verdict,
            "checked_at": report["checked_at"],
            "method": method,
            "report": "reports/source-check.json",
        }

    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    prompt_path.write_text(body, encoding="utf-8")
    meta.update({
        "schema_version": 3,
        "require_evidence": True,
        "evidence": counts,
        "evidence_report": "reports/source-check.json",
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
    })
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "count": payload["count"],
        "evidence": counts,
        "sha256": meta["sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
