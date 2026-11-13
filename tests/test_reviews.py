"""来源与翻译审核账本测试。"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from skynet_prompt.reviews import (
    ReviewError,
    build_ledger,
    load_ledger,
    validate_ledger,
)
from skynet_prompt.service import PromptService

ROOT = Path(__file__).resolve().parent.parent


def test_repository_review_ledger_covers_official_items():
    items = PromptService().items()
    ledger = load_ledger(ROOT / "reviews" / "review-ledger.json")
    validate_ledger(ledger, items)
    official = {
        item["id"] for item in items
        if item["evidence"]["verdict"] in {"verbatim", "paraphrase"}
    }
    assert set(ledger["items"]) == official
    assert len(ledger["items"]) == 34


def test_unverified_item_cannot_be_approved():
    decisions = {
        "schema_version": 1,
        "reviewer": {"id": "test", "kind": "ai-assisted"},
        "method": "test",
        "safety_method": "test",
        "reviewed_at": "2026-11-12T00:00:00+08:00",
        "approved_items": ["fx-outcome-01"],
    }
    try:
        build_ledger(decisions, PromptService().items())
    except ReviewError as exc:
        assert "未核实条目" in str(exc)
    else:
        raise AssertionError("未核实条目不应通过正式审核")


def test_changed_content_invalidates_review():
    items = PromptService().items()
    ledger = load_ledger(ROOT / "reviews" / "review-ledger.json")
    changed = copy.deepcopy(items)
    next(item for item in changed if item["id"] == "kp-verify-18")["zh"] += " 改"
    try:
        validate_ledger(ledger, changed)
    except ReviewError as exc:
        assert "旧审核已失效" in str(exc)
    else:
        raise AssertionError("正文改变后旧审核应该失效")


def test_decisions_are_json():
    data = json.loads(
        (ROOT / "reviews" / "review-decisions.json").read_text(encoding="utf-8")
    )
    assert data["reviewer"]["id"] == "codex-agent"
    assert data["reviewer"]["kind"] == "ai-assisted"
