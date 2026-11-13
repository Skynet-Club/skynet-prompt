#!/usr/bin/env python3
"""从内置快照导出发布包；unverified 条目不进入正式产物。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt import __version__  # noqa: E402
from skynet_prompt.catalog import BuiltinPromptSource, PromptCatalog  # noqa: E402
from skynet_prompt.reviews import load_ledger, validate_ledger  # noqa: E402
from skynet_prompt.safety import RULE_VERSION, scan_item  # noqa: E402
from skynet_prompt.signing import SignatureError, sign_manifest  # noqa: E402
from skynet_prompt.source_snapshots import (  # noqa: E402
    SourceSnapshotError,
    snapshot_digest,
)

SOURCES = ROOT / "reports" / "sources"
SOURCE_MANIFEST = SOURCES / "index.json"
REVIEW_LEDGER = ROOT / "reviews" / "review-ledger.json"


def pack_item(item: dict, review_record: dict | None) -> dict:
    source = dict(item["source"])
    source["language"] = "en"
    try:
        source["snapshot_sha256"] = snapshot_digest(SOURCE_MANIFEST, source["url"])
    except SourceSnapshotError as exc:
        raise SystemExit(str(exc)) from exc
    safety = scan_item(item)
    reviewed = review_record or {}
    return {
        **item,
        "source": source,
        "review": {
            "source": reviewed.get("source", "unreviewed"),
            "translation": reviewed.get("translation", "unreviewed"),
            "safety": reviewed.get("safety", "unreviewed"),
        },
        "safety": {
            "status": safety["status"],
            "flags": safety["flags"],
            "rule_version": RULE_VERSION,
            "automatic_only": True,
        },
        "insertion": {
            "policy": "exact-zh",
        },
        "translations": [{
            "language": "zh-CN",
            "text": item["zh"],
            "status": "reviewed" if reviewed else "unreviewed",
            "reviewer": reviewed.get("reviewer", {}) if reviewed else {},
        }],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "official")
    parser.add_argument("--channel", choices=["dev", "canary", "stable"], default="dev")
    parser.add_argument("--private-key", type=Path)
    parser.add_argument("--key-id", default="skynet-club-dev")
    args = parser.parse_args()

    source = BuiltinPromptSource().load()
    catalog = PromptCatalog([BuiltinPromptSource()]).load()
    audit = catalog.audit()
    ledger = load_ledger(REVIEW_LEDGER)
    validate_ledger(ledger, catalog.items())
    if audit["missing"]:
        raise SystemExit("存在缺少结构化证据的条目，拒绝导出：" + ", ".join(audit["missing"]))
    if audit["missing_rights"]:
        raise SystemExit("存在缺少版权字段的条目，拒绝导出：" + ", ".join(audit["missing_rights"]))

    items = [
        pack_item(item, ledger["items"].get(item["id"])) for item in catalog.items()
        if item["evidence"]["verdict"] in {"verbatim", "paraphrase"}
    ]
    if args.channel == "stable" and not args.private_key:
        raise SystemExit("stable 通道必须提供 --private-key 完成签名")
    payload = {
        "version": source.version,
        "count": len(items),
        "items": items,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    digest = hashlib.sha256(body.encode()).hexdigest()
    manifest = {
        "schema_version": 2,
        "id": "official",
        "name": "官方提示词包",
        "version": source.version,
        "channel": args.channel,
        "published_at": source.meta.get("fetched_at", "2026-11-12T00:00:00+08:00"),
        "items": "prompts.json",
        "sha256": digest,
        "digest": digest,
        "publisher": {
            "id": "skynet-club",
            "name": "Skynet Club",
        },
        "signature": None,
        "min_client_version": __version__,
        "license_summary": {
            "default": "not-declared",
            "redistribution": "excerpt-only",
        },
        "require_evidence": True,
    }
    if args.private_key:
        try:
            manifest = sign_manifest(
                manifest,
                args.private_key.expanduser(),
                key_id=args.key_id,
            )
        except SignatureError as exc:
            raise SystemExit(str(exc)) from exc
    official_meta = {
        **manifest,
        "count": len(items),
        "evidence": {
            verdict: sum(1 for item in items if item["evidence"]["verdict"] == verdict)
            for verdict in ("verbatim", "paraphrase", "unverified")
        },
        "rights": {
            "short-quotation-with-attribution": sum(
                1 for item in items
                if item["source"]["rights_basis"] == "short-quotation-with-attribution"
            ),
        },
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "prompts.json").write_text(body, encoding="utf-8")
    (args.out / "pack.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out / "meta.json").write_text(
        json.dumps(official_meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "count": len(items),
        "sha256": digest,
        "excluded": audit["evidence"]["unverified"],
        "rights": official_meta["rights"],
        "signed": bool(manifest.get("signature")),
        "key_id": (manifest.get("signature") or {}).get("key_id"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
