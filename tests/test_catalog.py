"""提示词包扩展接口：不依赖 prompt_toolkit。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from skynet_prompt.catalog import (
    PromptCatalog,
    PromptDataError,
    PromptPack,
    default_catalog,
)


def _item(item_id: str = "team-verify-01") -> dict:
    return {
        "id": item_id,
        "cat": "verify",
        "author": "Team",
        "date": "2026-11-12",
        "url": "https://example.com/source",
        "en": "State the acceptance check.",
        "zh": "先写清楚验收标准。",
        "nature": "本人原文",
    }


def _write_pack(root: Path, *, pack_id: str = "team", item_id: str | None = None) -> Path:
    root.mkdir(parents=True)
    prompt_path = root / "prompts.json"
    prompt_path.write_text(
        json.dumps(
            {
                "version": "1",
                "count": 1,
                "items": [_item(item_id or f"{pack_id}-verify-01")],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    (root / "pack.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": pack_id,
                "name": f"{pack_id} pack",
                "version": "1",
                "items": "prompts.json",
                "sha256": digest,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return root / "pack.json"


class MemorySource:
    def __init__(self, pack: PromptPack) -> None:
        self.pack = pack

    def load(self) -> PromptPack:
        return self.pack


def _set_packs(value: str | None):
    old = os.environ.get("SKYNET_PROMPT_PACKS")
    if value is None:
        os.environ.pop("SKYNET_PROMPT_PACKS", None)
    else:
        os.environ["SKYNET_PROMPT_PACKS"] = value
    return old


def _restore_packs(old: str | None) -> None:
    if old is None:
        os.environ.pop("SKYNET_PROMPT_PACKS", None)
    else:
        os.environ["SKYNET_PROMPT_PACKS"] = old


def test_default_catalog_keeps_builtin_pack():
    loaded = default_catalog().load()
    assert len(loaded.items()) == 42
    assert loaded.packs()[0].id == "builtin"


def test_external_pack_joins_the_same_catalog(tmp_path: Path):
    manifest = _write_pack(tmp_path / "team")
    old = _set_packs(str(manifest))
    try:
        loaded = default_catalog().load()
        assert len(loaded.items()) == 43
        assert [pack.id for pack in loaded.packs()] == ["builtin", "team"]
        assert loaded.pack_id("team-verify-01") == "team"
    finally:
        _restore_packs(old)


def test_custom_source_can_use_the_same_interface():
    pack = PromptPack(
        id="memory",
        name="Memory",
        version="1",
        items=[_item("memory-verify-01")],
        sha256="local",
    )
    loaded = PromptCatalog([MemorySource(pack)]).load()
    assert loaded.items()[0]["id"] == "memory-verify-01"


def test_duplicate_item_ids_are_rejected(tmp_path: Path):
    first = _write_pack(tmp_path / "first", pack_id="first", item_id="shared-id")
    second = _write_pack(tmp_path / "second", pack_id="second", item_id="shared-id")
    old = _set_packs(os.pathsep.join((str(first), str(second))))
    try:
        try:
            default_catalog().load()
        except PromptDataError as exc:
            assert "提示词 id 重复" in str(exc)
        else:
            raise AssertionError("重复 id 应该失败")
    finally:
        _restore_packs(old)


def test_bad_hash_is_rejected(tmp_path: Path):
    manifest = _write_pack(tmp_path / "bad-hash")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    old = _set_packs(str(manifest))
    try:
        try:
            default_catalog().load()
        except PromptDataError as exc:
            assert "sha256 不匹配" in str(exc)
        else:
            raise AssertionError("错误 hash 应该失败")
    finally:
        _restore_packs(old)


def test_audit_reports_frozen_evidence_counts():
    audit = default_catalog().audit()
    assert audit["ok"] is True
    assert audit["official_ready"] is False
    assert audit["evidence"] == {"paraphrase": 12, "unverified": 8, "verbatim": 22}
    assert audit["rights"] == {
        "explicit-license": 10,
        "short-quotation-with-attribution": 32,
    }
    assert audit["missing_rights"] == []


def test_required_evidence_rejects_legacy_item():
    pack = PromptPack(
        id="strict",
        name="Strict",
        version="1",
        items=[_item("strict-verify-01")],
        sha256="local",
        require_evidence=True,
    )
    try:
        PromptCatalog([MemorySource(pack)]).load()
    except PromptDataError as exc:
        assert "source.quote/source.url" in str(exc)
    else:
        raise AssertionError("缺失证据的严格包应该失败")


def test_required_evidence_rejects_item_without_rights():
    item = _item("strict-rights-01")
    item["source"] = {
        "quote": item["en"],
        "url": item["url"],
    }
    item["evidence"] = {
        "verdict": "verbatim",
        "checked_at": "2026-11-12T00:00:00+08:00",
    }
    pack = PromptPack(
        id="strict-rights",
        name="Strict rights",
        version="1",
        items=[item],
        sha256="local",
        require_evidence=True,
    )
    try:
        PromptCatalog([MemorySource(pack)]).load()
    except PromptDataError as exc:
        assert "缺少版权字段" in str(exc)
    else:
        raise AssertionError("缺失版权字段的严格包应该失败")
