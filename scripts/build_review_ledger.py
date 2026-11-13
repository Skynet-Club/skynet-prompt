#!/usr/bin/env python3
"""从人工/AI 审核决定生成内容摘要绑定的审核账本。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.reviews import build_ledger  # noqa: E402
from skynet_prompt.service import PromptService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--decisions",
        type=Path,
        default=ROOT / "reviews" / "review-decisions.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reviews" / "review-ledger.json",
    )
    args = parser.parse_args()

    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
    ledger = build_ledger(decisions, PromptService().items())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "reviewed": len(ledger["items"]),
        "reviewer": decisions["reviewer"],
        "method": decisions["method"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
