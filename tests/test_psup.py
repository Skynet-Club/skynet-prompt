"""psup 命令行：真跑子进程，断言输出（不是导入后调函数，那是另一回事）。"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PSUP = REPO / "psup"


def run(*args: str, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PSUP), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def cells(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in text)


def test_list_is_four_tab_fields():
    out = run("list")
    assert out.returncode == 0, out.stderr
    rows = [line.split("\t") for line in out.stdout.strip().splitlines()]
    assert len(rows) == 42
    assert all(len(r) == 4 for r in rows), [r for r in rows if len(r) != 4]
    ids = [r[0] for r in rows]
    assert len(set(ids)) == 42, "id 必须唯一"


def test_list_filters_by_category_name():
    out = run("list", "验收")
    assert out.returncode == 0
    rows = out.stdout.strip().splitlines()
    assert len(rows) == 9, rows
    assert all("定验收" in r for r in rows)


def test_json_listing_round_trips():
    out = run("list", "--json")
    payload = json.loads(out.stdout)
    assert len(payload) == 42
    assert {"id", "cat", "author", "date", "url", "en", "zh"} <= set(payload[0])


def test_show_prints_every_section_and_fits_60_cells():
    first = run("list").stdout.split("\t")[0]
    out = run("show", first)
    assert out.returncode == 0, out.stderr
    for label in ("原文", "中文"):
        assert label in out.stdout
    too_wide = [ln for ln in out.stdout.splitlines() if cells(ln) > 60]
    assert not too_wide, too_wide


def test_print_returns_the_exact_text():
    out = run("list", "--json")
    item = json.loads(out.stdout)[0]
    got = run("print", item["id"]).stdout.rstrip("\n")
    assert got == item["zh"]
    assert run("print", item["id"], "--field", "en").stdout.rstrip("\n") == item["en"]
    assert run("print", item["id"], "--lang", "zh-CN").stdout.rstrip("\n") == item["zh"]


def test_selftest_is_green_and_matches_disk_hash():
    out = run("selftest")
    assert out.returncode == 0, out.stdout + out.stderr
    result = json.loads(out.stdout)
    assert result["ok"] is True
    assert result["count"] == 42 and result["cats"] == 9
    assert result["sha256"] == result["meta_sha256"]


def test_bare_words_mean_list():
    out = run("验收")
    assert out.returncode == 0, out.stderr
    assert len(out.stdout.strip().splitlines()) == 9


def test_unknown_id_fails_loudly():
    out = run("show", "no-such-id")
    assert out.returncode != 0
    assert "no-such-id" in (out.stdout + out.stderr)


def test_pack_listing_exposes_extension_surface():
    out = run("packs", "--json")
    assert out.returncode == 0, out.stderr
    packs = json.loads(out.stdout)
    assert packs[0]["id"] == "builtin"
    assert packs[0]["count"] == 42


def test_list_can_filter_the_builtin_pack():
    out = run("list", "--pack", "builtin")
    assert out.returncode == 0, out.stderr
    assert len(out.stdout.strip().splitlines()) == 42


def test_external_pack_is_visible_through_psup(tmp_path: Path):
    prompt_path = tmp_path / "prompts.json"
    prompt_path.write_text(json.dumps({
        "version": "1",
        "count": 1,
        "items": [{
            "id": "team-verify-99",
            "cat": "verify",
            "author": "Team",
            "date": "2026-11-12",
            "url": "https://example.com/source",
            "en": "State the acceptance check.",
            "zh": "先写清楚验收标准。",
        }],
    }, ensure_ascii=False), encoding="utf-8")
    digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    (tmp_path / "pack.json").write_text(json.dumps({
        "schema_version": 1,
        "id": "team",
        "name": "Team",
        "version": "1",
        "items": "prompts.json",
        "sha256": digest,
    }), encoding="utf-8")
    env = dict(os.environ, SKYNET_PROMPT_PACKS=str(tmp_path))

    packs = run("packs", "--json", env=env)
    assert packs.returncode == 0, packs.stderr
    assert [pack["id"] for pack in json.loads(packs.stdout)] == ["builtin", "team"]

    listing = run("list", "--pack", "team", env=env)
    assert listing.returncode == 0, listing.stderr
    assert listing.stdout.startswith("team-verify-99\t")


def test_audit_reports_evidence_classes():
    out = run("audit", "--json")
    assert out.returncode == 0, out.stderr
    audit = json.loads(out.stdout)
    assert audit["evidence"] == {"paraphrase": 12, "unverified": 8, "verbatim": 22}
    assert audit["missing"] == []


def test_list_supports_category_and_limit_filters():
    out = run("list", "--category", "定验收", "--limit", "2")
    assert out.returncode == 0, out.stderr
    rows = out.stdout.strip().splitlines()
    assert len(rows) == 2
    assert all("定验收" in row for row in rows)


def test_capability_manifest_is_machine_readable():
    out = run("capabilities", "--json")
    assert out.returncode == 0, out.stderr
    manifest = json.loads(out.stdout)
    surfaces = {row["id"]: row for row in manifest["surfaces"]}
    assert manifest["platforms"]["supported"] == ["linux"]
    assert manifest["platforms"]["verified"] == ["ubuntu"]
    assert manifest["platforms"]["planned"] == ["windows", "macos"]
    assert manifest["experience"]["trigger"] == "；；"
    assert manifest["experience"]["aliases"] == [";;"]
    assert manifest["experience"]["literal_escape"] == "；；；"
    assert surfaces["hermes"]["level"] == "A"
    assert "insert" in surfaces["hermes"]["capabilities"]
    assert surfaces["opencode"]["level"] == "B"
    assert surfaces["opencode"]["status"] == "shell-verified-tui-unverified"
    assert "insert" not in surfaces["opencode"]["capabilities"]
    assert surfaces["pi"]["status"] == "shell-verified-package-installed"
    assert surfaces["claude-code"]["status"] == "skill-hook-mcp-installed-mcp-health-blocked"
    assert surfaces["copilot"]["status"] == "skill-mcp-installed-auth-blocked"
    assert surfaces["dsh"]["status"] == "headless-and-web-verified"
    assert surfaces["1agent"]["status"] == "terminal-tool-verified"
    assert surfaces["desktop-gui"]["status"] == "planned"


def test_version_is_consistent_across_cli_and_packages():
    from skynet_prompt import __version__

    out = run("version")
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == __version__

    package = json.loads((REPO / "package.json").read_text(encoding="utf-8"))
    plugin = json.loads(
        (REPO / "adapters" / "opencode-plugin" / "package.json").read_text(encoding="utf-8")
    )
    assert package["version"] == __version__
    assert plugin["version"] == __version__


def test_categories_are_machine_readable():
    out = run("categories", "--json")
    assert out.returncode == 0, out.stderr
    categories = json.loads(out.stdout)
    assert len(categories) == 9
    assert sum(row["count"] for row in categories) == 42
