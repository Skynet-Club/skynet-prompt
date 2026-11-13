#!/usr/bin/env python3
"""扫描当前提示词快照并写出确定性安全报告。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.safety import RULE_VERSION, scan_item  # noqa: E402
from skynet_prompt.service import PromptService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "safety.json")
    args = parser.parse_args()

    items = PromptService().items()
    rows = [
        {"id": item["id"], **scan_item(item)}
        for item in items
    ]
    flags = sum(len(row["flags"]) for row in rows)
    report = {
        "ok": True,
        "rule_version": RULE_VERSION,
        "count": len(rows),
        "passed": sum(1 for row in rows if row["status"] == "passed"),
        "needs_review": sum(1 for row in rows if row["status"] == "needs-review"),
        "flag_count": flags,
        "items_digest": hashlib.sha256(
            json.dumps(items, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "count": report["count"],
        "passed": report["passed"],
        "needs_review": report["needs_review"],
        "flag_count": flags,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
