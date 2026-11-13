"""Fabric v1.4.568 新增内容与 MIT 许可测试。"""

from __future__ import annotations

import json
from pathlib import Path

from skynet_prompt.service import PromptService

ROOT = Path(__file__).resolve().parent.parent


def test_ten_fabric_items_are_published():
    manifest = json.loads(
        (ROOT / "imports" / "fabric-v1.4.568.json").read_text(encoding="utf-8")
    )
    service = PromptService()
    for source_item in manifest["items"]:
        item = service.get(source_item["id"])
        assert item["source"]["license"] == "MIT"
        assert item["source"]["rights_basis"] == "explicit-license"
        assert item["evidence"]["verdict"] == "verbatim"
        snapshot = (
            ROOT
            / "reports"
            / "sources"
            / "fabric-v1.4.568"
            / source_item["snapshot"]
        ).read_text(encoding="utf-8")
        assert source_item["en"] in snapshot


def test_fabric_license_is_retained():
    text = (ROOT / "licenses" / "fabric-MIT.txt").read_text(encoding="utf-8")
    assert text.startswith("MIT License")
    assert "Permission is hereby granted" in text
