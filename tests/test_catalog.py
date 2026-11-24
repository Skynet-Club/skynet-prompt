"""官方包：条数、sha、搜索和审计。"""

from __future__ import annotations

from skynet_prompt.catalog import PromptDataError, default_catalog


def test_library_keeps_all_content():
    catalog = default_catalog().load()
    assert len(catalog.items()) == 42
    assert len(catalog.categories()) == 9
    assert sum(row["count"] for row in catalog.categories()) == 42
    assert all(row["count"] > 0 for row in catalog.categories())


def test_meta_and_sha_match():
    catalog = default_catalog().load()
    meta = catalog.meta()
    assert meta["count"] == 42
    assert meta["official_count"] == 22
    assert meta["sha256"] == catalog.sha256


def test_audit_is_ready_for_the_official_subset():
    audit = default_catalog().load().audit()
    assert audit["ok"] is True
    assert audit["official_ready"] is True
    assert audit["official_count"] == 22
    assert audit["evidence"] == {"verbatim": 22, "paraphrase": 12, "unverified": 8}
    assert audit["missing"] == []
    assert audit["missing_rights"] == []


def test_search_and_get():
    catalog = default_catalog().load()
    hits = catalog.search("验收")
    assert hits
    first = catalog.get(hits[0]["id"])
    assert first["id"] == hits[0]["id"]
    assert catalog.search(category="定验收")
    assert catalog.search(query="验收", category="定验收")


def test_unknown_id_fails():
    try:
        default_catalog().load().get("missing")
    except PromptDataError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("unknown id should fail")
