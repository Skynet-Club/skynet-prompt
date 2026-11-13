"""来源快照 manifest 与哈希测试。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from skynet_prompt.service import PromptService
from skynet_prompt.source_snapshots import verify_manifest

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "reports" / "sources"


def test_repository_source_manifest_matches_snapshots():
    urls = {item["url"] for item in PromptService().items()}
    result = verify_manifest(SOURCES / "index.json", urls)
    assert result["ok"], result["errors"]
    assert result["schema_version"] == 1
    assert result["checked"] == len(urls)


def test_snapshot_tamper_is_detected(tmp: Path):
    copied = tmp / "sources"
    shutil.copytree(SOURCES, copied)
    manifest = json.loads((copied / "index.json").read_text(encoding="utf-8"))
    url, entry = next(iter(manifest["sources"].items()))
    target = copied / entry["file"]
    target.write_bytes(target.read_bytes() + b"\nchanged")
    result = verify_manifest(copied / "index.json", {url})
    assert not result["ok"]
    assert any("sha256 不匹配" in error for error in result["errors"])


def test_legacy_manifest_is_not_complete(tmp: Path):
    path = tmp / "index.json"
    path.write_text(
        json.dumps({"https://example.com": {"file": "missing.html"}}),
        encoding="utf-8",
    )
    result = verify_manifest(path, {"https://example.com"})
    assert not result["ok"]
    assert result["schema_version"] == 0
