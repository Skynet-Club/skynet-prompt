"""独立 Advisor 的确定性排序测试。"""

from __future__ import annotations

from skynet_prompt.advisor import suggest
from skynet_prompt.service import PromptService


def test_acceptance_query_prefers_verify_items():
    items = PromptService().items()
    rows = suggest(items, "验收 测试", limit=5)
    assert rows
    assert rows[0]["cat"] == "verify"
    assert any(reason.startswith("keyword:") for reason in rows[0]["reasons"])


def test_advisor_does_not_rewrite_text():
    items = PromptService().items()
    target = next(row for row in items if row["id"] == "kp-verify-18")
    rows = suggest(items, "验收 完成", limit=20)
    result = next(row for row in rows if row["id"] == target["id"])
    assert result["zh"] == target["zh"]
    assert result["score"] > 0


def test_zero_match_returns_empty():
    assert suggest(PromptService().items(), "zzzz-not-found", limit=5) == []


def test_unverified_and_high_risk_items_are_not_suggested():
    rows = suggest(PromptService().items(), "验收 DGX 密码", limit=20)
    assert all(row["id"] != "kp-verify-16" for row in rows)
    assert all(row["evidence"]["verdict"] != "unverified" for row in rows)
