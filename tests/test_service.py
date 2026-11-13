"""Core 查询服务：CLI 与 MCP 的共同契约。"""

from __future__ import annotations

from skynet_prompt.service import PromptService, PromptServiceError


def test_search_by_category_and_pack():
    service = PromptService()
    rows = service.search(category="定验收", pack="builtin")
    assert len(rows) == 9
    assert all(row["cat"] == "verify" for row in rows)


def test_search_applies_limit_and_all_words():
    service = PromptService()
    rows = service.search("验收 裁判", limit=2)
    assert len(rows) <= 2
    assert all("裁判" in row["zh"] for row in rows)


def test_compose_is_deterministic():
    service = PromptService()
    ids = [item["id"] for item in service.search(category="verify", limit=2)]
    result = service.compose(ids)
    expected = "\n\n".join(service.get(item_id)["zh"] for item_id in ids)
    assert result["text"] == expected


def test_unknown_values_fail_loudly():
    service = PromptService()
    for call in (
        lambda: service.search(pack="missing"),
        lambda: service.search(category="missing"),
        lambda: service.get("missing"),
        lambda: service.compose([]),
    ):
        try:
            call()
        except PromptServiceError:
            pass
        else:
            raise AssertionError("非法输入应该失败")


def test_categories_keep_stable_order():
    categories = PromptService().categories()
    assert [row["key"] for row in categories][:2] == ["outcome", "think_first"]
    assert sum(row["count"] for row in categories) == 42
