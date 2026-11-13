"""产物生成的测试：正文逐字节、清单齐全、漂移必被发现。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from skynet_prompt.build import build, check, load_items, render, slug
from skynet_prompt.content import CONTENT, ORIGIN_LABELS

REPO = Path(__file__).resolve().parent.parent


def _body(data: bytes) -> str:
    text = data.decode("utf-8")
    assert text.startswith("---\n")
    end = text.index("\n---\n", 4)
    return text[end + 5:]


def test_repository_artifacts_are_current():
    result = check()
    assert result["ok"], result
    assert result["expected"] == 133


def test_counts():
    files = render()
    pi = [p for p in files if p.startswith("adapters/pi/prompts/")]
    codex = [p for p in files if p.startswith("adapters/codex-plugin/skills/")]
    opencode = [p for p in files if p.startswith("adapters/opencode/commands/")]
    assert len(pi) == 42
    assert len(codex) == 43             # 42 条 + psup 索引技能
    assert len(opencode) == 43          # 42 条 + README
    assert "package.json" in files
    assert ".agents/plugins/marketplace.json" in files


def test_pi_bodies_are_exact():
    files = render()
    items = {item["id"]: item for item in load_items(CONTENT)}
    for item_id, item in items.items():
        path = f"adapters/pi/prompts/psup-{slug(item_id)}.md"
        assert _body(files[path]) == item["zh"]


def test_codex_bodies_are_exact():
    files = render()
    items = {item["id"]: item for item in load_items(CONTENT)}
    for item_id, item in items.items():
        path = f"adapters/codex-plugin/skills/psup-{slug(item_id)}/SKILL.md"
        body = _body(files[path])
        assert body == item["zh"]
        assert body != item["en"]


def test_opencode_bodies_are_exact():
    files = render()
    items = {item["id"]: item for item in load_items(CONTENT)}
    for item_id, item in items.items():
        path = f"adapters/opencode/commands/psup-{slug(item_id)}.md"
        assert _body(files[path]) == item["zh"]


def test_psup_index_skill_lists_categories():
    files = render()
    body = files["adapters/codex-plugin/skills/psup/SKILL.md"].decode("utf-8")
    assert "；；" in body
    assert "兼容的 `;;`" in body
    assert "disable-model-invocation" not in body
    assert "psup categories --json" in body
    assert "只列 9 个类目" in body
    for name in ("要结果", "先想清楚", "定验收", "别碰旁边的"):
        assert name in body
    assert "fx-outcome-01" in body


def test_trigger_protocol_accepts_canonical_and_ascii_aliases():
    from skynet_prompt.trigger import strip_leading_trigger

    assert strip_leading_trigger("；； 定验收") == "定验收"
    assert strip_leading_trigger(";; 定验收") == "定验收"
    assert strip_leading_trigger("；；；") is None
    assert strip_leading_trigger("普通消息") is None


def test_descriptions_carry_origin_badges():
    files = render()
    sample = files["adapters/pi/prompts/psup-kp-verify-18.md"].decode("utf-8")
    assert "中文直译" in sample
    assert ORIGIN_LABELS["compilation"] in sample


def test_pi_extension_is_declared():
    package = json.loads(render()["package.json"])
    assert package["pi"]["extensions"] == ["./adapters/pi-extension/index.ts"]
    assert (REPO / "adapters/pi-extension/index.ts").exists()


def test_manifests_are_valid_json():
    files = render()
    package = json.loads(files["package.json"])
    market = json.loads(files[".agents/plugins/marketplace.json"])
    plugin = json.loads(files["adapters/codex-plugin/.codex-plugin/plugin.json"])
    assert package["pi"]["prompts"] == ["./adapters/pi/prompts/*.md"]
    assert package["pi"]["extensions"] == ["./adapters/pi-extension/index.ts"]
    assert market["plugins"][0]["source"]["path"] == "./adapters/codex-plugin"
    assert plugin["skills"] == "./skills/"


def test_drift_is_detected(tmp: Path):
    files = render()
    for rel, data in files.items():
        if rel.startswith("adapters/pi/") or rel == "package.json":
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    target = tmp / "adapters/pi/prompts/psup-kp-verify-18.md"
    target.write_bytes(target.read_bytes() + b"x")
    result = check(tmp, hosts=("pi",), content_root=CONTENT)
    assert not result["ok"]
    assert "adapters/pi/prompts/psup-kp-verify-18.md" in result["different"]


def test_extra_files_are_removed(tmp: Path):
    files = render()
    for rel, data in files.items():
        if rel.startswith("adapters/pi/") or rel == "package.json":
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    extra = tmp / "adapters/pi/prompts/stale.md"
    extra.write_text("stale", encoding="utf-8")
    result = build(tmp, hosts=("pi",), content_root=CONTENT)
    assert "adapters/pi/prompts/stale.md" in result["removed"]
    assert not extra.exists()


def test_render_is_deterministic():
    assert render() == render()
