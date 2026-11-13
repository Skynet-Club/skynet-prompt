#!/usr/bin/env python3
"""为已生成的 Pack 创建签名发布审批。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.approvals import ApprovalError, create_approval  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--as", dest="approver", required=True)
    parser.add_argument("--role", choices=["reviewer", "publisher"], required=True)
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    args = parser.parse_args()
    try:
        approval = create_approval(
            args.release,
            approver=args.approver,
            role=args.role,
            private_key=args.private_key,
            key_id=args.key_id,
        )
    except ApprovalError as exc:
        print(f"approve: {exc}", file=sys.stderr)
        return 1
    out = args.release / "approvals" / f"{approval['approval_id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(approval, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "out": str(out),
        "approval_id": approval["approval_id"],
        "approver": approval["approver"],
        "role": approval["role"],
        "pack_sha256": approval["pack_sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
