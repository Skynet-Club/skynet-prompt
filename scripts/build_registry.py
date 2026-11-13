#!/usr/bin/env python3
"""从已签名 v2 Pack 构建本地 Registry。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.registry import RegistryError, build_registry, verify_registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "registry")
    parser.add_argument("--id", default="skynet-club")
    parser.add_argument("--trust", type=Path, default=ROOT / "trust" / "keys.json")
    args = parser.parse_args()
    try:
        registry = build_registry(
            args.out,
            args.release,
            registry_id=args.id,
            trust_path=args.trust,
        )
        result = verify_registry(args.out, registry, trust_path=args.trust)
    except RegistryError as exc:
        print(f"registry: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "ok": result["ok"],
        "out": str(args.out),
        "registry_id": result["registry_id"],
        "packs": result["packs"],
        "errors": result["errors"],
    }, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
