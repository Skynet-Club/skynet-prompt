"""完整 M1 发布流水线测试。"""

from __future__ import annotations

import json
from pathlib import Path

from skynet_prompt.release import ReleaseError, release

ROOT = Path(__file__).resolve().parent.parent


def test_dev_release_pipeline(tmp: Path):
    out = tmp / "release"
    report = release(ROOT, out, channel="dev")
    assert report["ok"] is True
    assert report["channel"] == "dev"
    assert report["item_count"] == 34
    assert report["reviewed"] == 34
    assert report["source_snapshots"] >= 1
    assert report["git_commit"]

    persisted = json.loads((out / "release-report.json").read_text(encoding="utf-8"))
    assert persisted["pack_sha256"] == report["pack_sha256"]
    assert (out / "pack.json").exists()
    assert (out / "prompts.json").exists()
    assert (out / "meta.json").exists()


def test_stable_release_is_blocked_until_signing(tmp: Path):
    try:
        release(ROOT, tmp / "stable", channel="stable")
    except ReleaseError as exc:
        assert "stable" in str(exc)
        assert "签名" in str(exc)
    else:
        raise AssertionError("未实现签名前 stable 发布应该失败")
