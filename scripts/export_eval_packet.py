#!/usr/bin/env python3
"""把真实 A/B 结果导出为匿名人工评审包。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        type=Path,
        default=ROOT / "evaluations" / "results-advisor-2026-11-13.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "dist" / "evaluation-packets",
    )
    args = parser.parse_args()
    data = json.loads(args.results.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    key = {}
    for row in data["rows"]:
        baseline_first = hashlib.sha256(
            f"packet:{row['id']}".encode("utf-8")
        ).digest()[0] % 2 == 0
        first = row["baseline"] if baseline_first else row["augmented"]
        second = row["augmented"] if baseline_first else row["baseline"]
        key[row["id"]] = {
            "A": "baseline" if baseline_first else "augmented",
            "B": "augmented" if baseline_first else "baseline",
        }
        text = (
            f"# {row['id']}\n\n"
            f"## 任务\n\n{row['task']}\n\n"
            f"## Criteria\n\n" + "\n".join(f"- {item}" for item in row["criteria"]) +
            f"\n\n## 回答 A\n\n{first}\n\n"
            f"## 回答 B\n\n{second}\n\n"
            "## 评审\n\n请填写：winner = A / B / tie\n\nreason：\n"
        )
        (args.out / f"{row['id']}.md").write_text(text, encoding="utf-8")
    (args.out / "answer-key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "packets": len(key),
        "answer_key": str(args.out / "answer-key.json"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
