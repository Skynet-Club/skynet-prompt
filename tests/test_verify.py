"""content/ 冻结层的测试：逐字节迁移、篡改必失败。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from skynet_prompt.content import CONTENT, LEGACY, verify

REPO = Path(__file__).resolve().parent.parent


def _copy(tmp: Path) -> tuple[Path, Path]:
    content = tmp / "content"
    legacy = tmp / "data"
    shutil.copytree(CONTENT, content)
    shutil.copytree(LEGACY, legacy)
    return content, legacy


def test_repository_content_verifies():
    result = verify()
    assert result["ok"], result["errors"]
    assert result["count"] == 42
    assert result["origins"] == {"verbatim": 22, "compilation": 12, "unverified": 8}
    assert result["excerpts"] == 24
    assert result["legacy"] == "match"


def test_migration_is_byte_exact():
    payload = json.loads((LEGACY / "prompts.json").read_text(encoding="utf-8"))
    for item in payload["items"]:
        base = CONTENT / "items" / item["id"]
        assert (base / "zh.txt").read_bytes() == item["zh"].encode("utf-8")
        assert (base / "en.txt").read_bytes() == item["en"].encode("utf-8")


def test_cat_names_are_present():
    index = json.loads((CONTENT / "index.json").read_text(encoding="utf-8"))
    assert len(index["cat_names"]) == 9
    assert index["cat_names"]["verify"] == "定验收"


def test_detects_text_drift(tmp: Path):
    content, legacy = _copy(tmp)
    target = content / "items" / "kp-verify-18" / "zh.txt"
    target.write_bytes(target.read_bytes() + "改".encode("utf-8"))
    result = verify(content, legacy)
    assert not result["ok"]
    assert any("kp-verify-18" in e and "zh.txt" in e for e in result["errors"])
    assert result["legacy"] == "mismatch"


def test_detects_meta_tamper(tmp: Path):
    content, legacy = _copy(tmp)
    meta_path = content / "items" / "kp-verify-18" / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["origin"] = "verbatim"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = verify(content, legacy)
    assert not result["ok"]
    assert any("index.origin" in e for e in result["errors"])


def test_detects_rights_tamper(tmp: Path):
    content, legacy = _copy(tmp)
    meta_path = content / "items" / "kp-verify-18" / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["source"]["license"] = "MIT"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = verify(content, legacy)
    assert not result["ok"]
    assert any("index.source" in e for e in result["errors"])
    assert any("digest" in e for e in result["errors"])


def test_detects_missing_item(tmp: Path):
    content, legacy = _copy(tmp)
    shutil.rmtree(content / "items" / "kp-verify-18")
    result = verify(content, legacy)
    assert not result["ok"]
    assert any("kp-verify-18" in e for e in result["errors"])


def test_detects_index_tamper(tmp: Path):
    content, legacy = _copy(tmp)
    index_path = content / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["count"] = 31
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = verify(content, legacy)
    assert not result["ok"]
    assert any("index.count" in e for e in result["errors"])
