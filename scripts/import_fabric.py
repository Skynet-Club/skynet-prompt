#!/usr/bin/env python3
"""把固定版本、MIT 许可的 Fabric prompt 导入候选和内容快照。"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.candidates import (  # noqa: E402
    add_candidate,
    load_store,
    save_store,
    transition_candidate,
)

IMPORT = ROOT / "imports" / "fabric-v1.4.568.json"
DATA = ROOT / "data"
SOURCES = ROOT / "reports" / "sources"
SOURCE_ROOT = SOURCES / "fabric-v1.4.568"
CHECKED_AT = "2026-11-12T21:45:00+08:00"
CONTENT_VERSION = "2026-11-13"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    manifest = json.loads(IMPORT.read_text(encoding="utf-8"))
    source_meta = manifest["source"]
    prompt_path = DATA / "prompts.json"
    meta_path = DATA / "meta.json"
    payload = json.loads(prompt_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    candidates_path = ROOT / "candidates" / "candidates.json"
    candidate_store = load_store(candidates_path)
    source_index_path = SOURCES / "index.json"
    source_index = json.loads(source_index_path.read_text(encoding="utf-8"))

    existing = {item["id"] for item in payload["items"]}
    added = []
    for source_item in manifest["items"]:
        snapshot_path = SOURCE_ROOT / source_item["snapshot"]
        snapshot = snapshot_path.read_text(encoding="utf-8")
        if source_item["en"] not in snapshot:
            raise SystemExit(f"{source_item['id']}: 精确原文不在快照中")
        if source_item["id"] in existing:
            continue

        submission = add_candidate(
            candidate_store,
            {
                "url": source_item["url"],
                "author": source_item["author"],
                "date": source_item["date"],
                "en": source_item["en"],
                "zh": source_item["zh"],
                "license": source_meta["license"],
                "language": "en",
            },
            submitted_by="import:fabric",
        )
        candidate_id = submission["candidate"]["id"]
        for status in ("sourced", "translated", "reviewed", "published"):
            transition_candidate(
                candidate_store,
                candidate_id,
                status,
                by="import:fabric",
                note=f"Fabric {source_meta['version']}",
            )

        item = {
            "id": source_item["id"],
            "cat": source_item["cat"],
            "author": source_item["author"],
            "date": source_item["date"],
            "url": source_item["url"],
            "en": source_item["en"],
            "zh": source_item["zh"],
            "nature": "项目原文",
            "excerpt": bool(source_item["excerpt"]),
            "source": {
                "quote": source_item["en"],
                "url": source_item["url"],
                "author": source_item["author"],
                "published_at": source_item["date"],
                "license": source_meta["license"],
                "rights_basis": "explicit-license",
                "redistribution": "full-text",
            },
            "evidence": {
                "verdict": "verbatim",
                "checked_at": CHECKED_AT,
                "method": "pinned-local-snapshot",
                "report": f"reports/sources/fabric-v1.4.568/{source_item['snapshot']}",
            },
        }
        payload["items"].append(item)
        added.append(item["id"])

        data = snapshot_path.read_bytes()
        source_index["sources"][source_item["url"]] = {
            "file": f"fabric-v1.4.568/{source_item['snapshot']}",
            "sha256": sha256(data),
            "size": len(data),
            "media_type": "text/markdown",
            "fetched_at": CHECKED_AT,
            "via": "github-api:pinned-tag",
            "license": source_meta["license"],
            "ok": True,
        }

    payload["version"] = CONTENT_VERSION
    payload["count"] = len(payload["items"])
    natures: dict[str, int] = {}
    rights: dict[str, int] = {}
    evidence: dict[str, int] = {}
    cats: dict[str, int] = {}
    for item in payload["items"]:
        nature = item.get("nature", "未核实")
        natures[nature] = natures.get(nature, 0) + 1
        basis = item["source"]["rights_basis"]
        rights[basis] = rights.get(basis, 0) + 1
        verdict = item["evidence"]["verdict"]
        evidence[verdict] = evidence.get(verdict, 0) + 1
        cats[item["cat"]] = cats.get(item["cat"], 0) + 1

    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    prompt_path.write_text(body, encoding="utf-8")
    meta.update({
        "version": CONTENT_VERSION,
        "count": payload["count"],
        "natures": natures,
        "rights": rights,
        "evidence": evidence,
        "excerpts": sum(1 for item in payload["items"] if item.get("excerpt")),
        "sha256": sha256(body.encode("utf-8")),
        "source": "Skynet editorial snapshot + Fabric v1.4.568",
        "fetched_at": CHECKED_AT,
    })
    for key in list(meta.get("cats", {})):
        meta["cats"][key]["count"] = cats.get(key, 0)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    source_index["generated_at"] = datetime.now(timezone(timedelta(hours=8))).isoformat(
        timespec="seconds"
    )
    source_index_path.write_text(
        json.dumps(source_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    save_store(candidates_path, candidate_store)

    decisions_path = ROOT / "reviews" / "review-decisions.json"
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    approved = decisions["approved_items"]
    for item_id in added:
        if item_id not in approved:
            approved.append(item_id)
    decisions_path.write_text(
        json.dumps(decisions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "added": added,
        "count": payload["count"],
        "version": CONTENT_VERSION,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
