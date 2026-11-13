#!/usr/bin/env python3
"""聚合多个独立 cross-model 盲评批次并计算符号检验。"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def binom_tail(n: int, k: int) -> float:
    if k <= 0:
        return 1.0
    return sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs="+", type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "evaluations" / "results-advisor-cross-model-30.json",
    )
    args = parser.parse_args()

    wins = {"baseline": 0, "augmented": 0, "tie": 0}
    rows = []
    for path in args.results:
        batch = json.loads(path.read_text(encoding="utf-8"))
        for row in batch["rows"]:
            winner = row["verdict"]["winner"]
            wins[winner] = wins.get(winner, 0) + 1
            rows.append({
                "batch": path.name,
                "id": row["id"],
                "selected_prompt_id": row.get("selected_prompt_id"),
                "winner": winner,
                "reason": row["verdict"].get("reason", ""),
            })
    decisive = wins["baseline"] + wins["augmented"]
    total = sum(wins.values())
    result = {
        "ok": True,
        "batches": [str(path) for path in args.results],
        "method": "cross-model blind pairwise",
        "total": total,
        "wins": wins,
        "decisive": decisive,
        "augmented_win_rate": round(wins["augmented"] / max(total, 1), 3),
        "decisive_win_rate": round(wins["augmented"] / max(decisive, 1), 3),
        "sign_test_p_non_ties": binom_tail(decisive, wins["augmented"]),
        "sign_test_p_all": binom_tail(total, wins["augmented"]),
        "rows": rows,
    }
    args.out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "total": total,
        "wins": wins,
        "decisive_win_rate": result["decisive_win_rate"],
        "p_non_ties": result["sign_test_p_non_ties"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
