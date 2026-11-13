#!/usr/bin/env python3
"""执行 skynet-prompt 的完整发布流水线。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.release import ReleaseError, release  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "release")
    parser.add_argument("--channel", choices=["dev", "canary", "stable"], default="dev")
    parser.add_argument("--private-key", type=Path)
    parser.add_argument("--key-id", default="skynet-club-dev")
    parser.add_argument("--approval", type=Path, action="append", default=[])
    parser.add_argument("--trust", type=Path, default=ROOT / "trust" / "keys.json")
    args = parser.parse_args()
    try:
        report = release(
            ROOT,
            args.out,
            channel=args.channel,
            private_key=args.private_key,
            key_id=args.key_id,
            approval_paths=args.approval,
            trust_path=args.trust,
        )
    except ReleaseError as exc:
        print(f"release: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
