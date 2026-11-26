"""官方包：条数、sha、搜索和审计。"""

from __future__ import annotations

from skynet_prompt.catalog import PromptDataError, default_catalog


def test_library_keeps_all_content():
    catalog = default_catalog().load()
    meta = catalog.meta()
    assert len(catalog.items()) == meta["count"]
    assert len(catalog.categories()) == 9
    assert sum(row["count"] for row in catalog.categories()) == meta["count"]
    assert all(row["count"] > 0 for row in catalog.categories())


def test_prompts_are_bilingual():
    for item in default_catalog().load().items():
        assert item["zh"].strip()
        assert item["en"].strip()


def test_scene_taxonomy():
    rows = default_catalog().load().categories()
    assert [row["name"] for row in rows] == [
        "加目标", "加深度", "加广度", "加约束",
        "加证据", "加检验", "加读者", "加执行", "加时间",
    ]
    assert [row["en"] for row in rows] == [
        "Goal", "Depth", "Breadth", "Constraints",
        "Evidence", "Check", "Reader", "Execution", "Time",
    ]
    assert all(row["count"] > 0 for row in rows)


def test_meta_and_sha_match():
    catalog = default_catalog().load()
    meta = catalog.meta()
    official = sum(
        1 for item in catalog.items()
        if item["evidence"]["verdict"] == "verbatim"
    )
    assert meta["count"] == len(catalog.items())
    assert meta["official_count"] == official
    assert meta["sha256"] == catalog.sha256


def test_audit_is_ready_for_the_official_subset():
    audit = default_catalog().load().audit()
    assert audit["ok"] is True
    assert audit["official_ready"] is True
    assert audit["official_count"] == sum(
        1 for item in default_catalog().load().items()
        if item["evidence"]["verdict"] == "verbatim"
    )
    assert sum(audit["evidence"].values()) == audit["count"]
    assert audit["missing"] == []
    assert audit["missing_rights"] == []


def test_search_and_get():
    catalog = default_catalog().load()
    hits = catalog.search("验证")
    assert hits
    first = catalog.get(hits[0]["id"])
    assert first["id"] == hits[0]["id"]
    assert catalog.search(category="加检验")
    assert catalog.search(query="测试", category="加检验")


def test_unknown_id_fails():
    try:
        default_catalog().load().get("missing")
    except PromptDataError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("unknown id should fail")
