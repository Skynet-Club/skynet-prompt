"""Prompt Pack v2 契约测试。"""

from __future__ import annotations

import copy
import hashlib

from skynet_prompt.pack_schema import (
    PackSchemaError,
    validate_items,
    validate_manifest,
)


def _item() -> dict:
    return {
        "id": "team-verify-01",
        "cat": "verify",
        "author": "Team",
        "date": "2026-11-12",
        "url": "https://example.com/source",
        "en": "State the acceptance check.",
        "zh": "先写清楚验收标准。",
        "source": {
            "quote": "State the acceptance check.",
            "url": "https://example.com/source",
            "author": "Team",
            "published_at": "2026-11-12",
            "language": "en",
            "license": "MIT",
            "rights_basis": "explicit-license",
            "redistribution": "full-text",
            "snapshot_sha256": "a" * 64,
        },
        "evidence": {
            "verdict": "verbatim",
            "checked_at": "2026-11-12T00:00:00+08:00",
        },
        "review": {
            "source": "reviewed",
            "translation": "reviewed",
            "safety": "reviewed",
        },
        "safety": {
            "status": "passed",
            "flags": [],
        },
        "insertion": {
            "policy": "exact-zh",
        },
    }


def test_v2_items_validate():
    items = validate_items({"version": "1", "count": 1, "items": [_item()]})
    assert items[0]["source"]["rights_basis"] == "explicit-license"


def test_v2_items_require_review():
    item = _item()
    del item["review"]
    try:
        validate_items({"version": "1", "count": 1, "items": [item]})
    except PackSchemaError as exc:
        assert "review" in str(exc)
    else:
        raise AssertionError("v2 条目缺少 review 应该失败")


def test_v2_manifest_validates_digest_and_channel():
    payload = b'{"version":"1","count":1,"items":[]}\n'
    digest = hashlib.sha256(payload).hexdigest()
    manifest = {
        "schema_version": 2,
        "id": "team",
        "name": "Team",
        "version": "1",
        "channel": "dev",
        "published_at": "2026-11-12T00:00:00+08:00",
        "items": "prompts.json",
        "sha256": digest,
        "digest": digest,
        "publisher": {"id": "team", "name": "Team"},
        "signature": None,
        "min_client_version": "0.2.0",
        "license_summary": {
            "default": "MIT",
            "redistribution": "full-text",
        },
        "require_evidence": True,
    }
    validate_manifest(manifest, digest)

    broken = copy.deepcopy(manifest)
    broken["channel"] = "production"
    try:
        validate_manifest(broken, digest)
    except PackSchemaError as exc:
        assert "发布通道" in str(exc)
    else:
        raise AssertionError("未知发布通道应该失败")
