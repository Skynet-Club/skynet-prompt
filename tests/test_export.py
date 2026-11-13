"""正式包导出：只允许有结构化证据且非 unverified 的条目。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from skynet_prompt.catalog import JsonPackSource

ROOT = Path(__file__).resolve().parent.parent


def test_official_export_excludes_unverified(tmp_path: Path):
    out = tmp_path / "official"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_official.py"), "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    pack = JsonPackSource(out).load()
    assert pack.id == "official"
    assert pack.require_evidence is True
    assert len(pack.items) == 34
    manifest = json.loads((out / "pack.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert manifest["channel"] == "dev"
    assert manifest["digest"] == manifest["sha256"]
    assert sum(
        item["source"]["rights_basis"] == "short-quotation-with-attribution"
        for item in pack.items
    ) == 24
    assert sum(
        item["source"]["rights_basis"] == "explicit-license"
        for item in pack.items
    ) == 10
    assert sum(
        item["source"]["redistribution"] == "excerpt-only"
        for item in pack.items
    ) == 24
    assert sum(
        item["source"]["redistribution"] == "full-text"
        for item in pack.items
    ) == 10
    assert all(item["review"]["source"] == "reviewed" for item in pack.items)
    assert all(item["review"]["translation"] == "reviewed" for item in pack.items)
    assert all(item["review"]["safety"] == "reviewed" for item in pack.items)
    assert all(item["insertion"]["policy"] == "exact-zh" for item in pack.items)
    assert all(
        item["translations"][0]["language"] == "zh-CN"
        for item in pack.items
    )
    assert all(item["translations"][0]["status"] == "reviewed" for item in pack.items)
    assert all(item["safety"]["automatic_only"] is True for item in pack.items)
    assert {item["evidence"]["verdict"] for item in pack.items} == {
        "verbatim",
        "paraphrase",
    }
    payload = json.loads((out / "prompts.json").read_text(encoding="utf-8"))
    assert payload["count"] == 34

    env = dict(os.environ, SKYNET_PROMPT_DATA=str(out))
    selftest = subprocess.run(
        [sys.executable, str(ROOT / "psup"), "selftest"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert selftest.returncode == 0, selftest.stderr
    result = json.loads(selftest.stdout)
    assert result["count"] == 34
    assert result["packs"][0]["id"] == "official"

    audit = subprocess.run(
        [sys.executable, str(ROOT / "psup"), "audit", "--json"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert audit.returncode == 0, audit.stderr
    assert json.loads(audit.stdout)["official_ready"] is True


def test_stable_channel_requires_human_reviews(tmp_path: Path):
    out = tmp_path / "stable"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_official.py"),
            "--out",
            str(out),
            "--channel",
            "stable",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "stable 通道必须提供" in proc.stderr
