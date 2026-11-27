"""管理后台的数据层：增删改、校验、sha 和备份。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from skynet_prompt.admin import AdminError, AdminStore


def make_store(tmp: Path) -> AdminStore:
    source = Path(__file__).resolve().parent.parent / "data"
    target = tmp / "data"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".backups"))
    return AdminStore(target)


def item(ident: str = "test-admin-01") -> dict:
    return {
        "id": ident,
        "cat": "goal",
        "author": "测试作者",
        "date": "2026-11-26",
        "url": "https://example.com/source",
        "zh": "中文测试正文。",
        "en": "English test body.",
        "nature": "未核实",
        "excerpt": False,
        "evidence": {"verdict": "unverified"},
        "source": {
            "license": "not-declared",
            "rights_basis": "short-quotation-with-attribution",
            "redistribution": "excerpt-only",
            "note": "",
        },
    }


def test_admin_crud_updates_meta_and_backup(tmp: Path):
    store = make_store(tmp)
    before = store.state()
    before_count = before["stats"]["count"]
    assert before_count > 0

    created = store.save_item(None, item())
    assert created["item"]["id"] == "test-admin-01"
    assert created["state"]["stats"]["count"] == before_count + 1
    assert (tmp / "data" / ".backups").is_dir()
    assert created["state"]["meta"]["sha256"] == created["state"]["sha256"]

    updated_payload = item("test-admin-02")
    updated = store.save_item("test-admin-01", updated_payload)
    assert updated["item"]["id"] == "test-admin-02"
    assert updated["state"]["stats"]["count"] == before_count + 1

    deleted = store.delete_item("test-admin-02")
    assert deleted["state"]["stats"]["count"] == before_count
    rows = json.loads((tmp / "data" / "prompts.json").read_text(encoding="utf-8"))["items"]
    assert not any(row["id"] == "test-admin-02" for row in rows)


def test_admin_rejects_bad_scene_and_duplicate_id(tmp: Path):
    store = make_store(tmp)
    bad = item()
    bad["cat"] = "missing"
    try:
        store.save_item(None, bad)
    except AdminError as exc:
        assert "场景" in str(exc)
    else:
        raise AssertionError("bad scene should fail")

    first = item("test-admin-01")
    store.save_item(None, first)
    try:
        store.save_item(None, first)
    except AdminError as exc:
        assert "已存在" in str(exc)
    else:
        raise AssertionError("duplicate id should fail")
