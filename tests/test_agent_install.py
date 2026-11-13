"""Agent 自安装契约：默认只读、显式执行、验证和卸载。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from skynet_prompt import __version__
from skynet_prompt.trigger import CANONICAL_TRIGGER
from skynet_prompt.trust import add_key

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "agent_install.py"


def run_agent(home: Path, *args: str) -> tuple[subprocess.CompletedProcess, dict]:
    env = dict(os.environ, HOME=str(home), PATH="/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return proc, json.loads(proc.stdout)


def test_manifest_matches_product_contract():
    manifest = json.loads((ROOT / "install-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["product"] == "skynet-prompt"
    assert manifest["version"] == __version__
    assert manifest["trigger"] == CANONICAL_TRIGGER
    assert manifest["safety"]["requires_sudo"] is False
    assert manifest["safety"]["reads_credentials"] is False
    assert manifest["safety"]["sends_prompts"] is False
    assert manifest["safety"]["plan_before_apply"] is True


def test_default_plan_is_read_only(tmp_path: Path):
    proc, report = run_agent(tmp_path, "--plan", "--adapter", "cli")
    assert proc.returncode == 0, proc.stderr
    assert report["ok"] is True
    assert report["mode"] == "plan"
    assert report["selected"] == ["cli"]
    assert report["changes"] == ["在 ~/.local/bin 创建 psup、psup-mcp、psupd 链接"]
    assert "--dry-run" in report["installer"]["command"]
    assert "--cli-only" in report["installer"]["command"]
    assert "sudo" not in report["commands"]["install"]
    assert "curl" not in report["commands"]["install"]
    assert not (tmp_path / ".local").exists()


def test_cli_apply_verifies_and_uninstalls(tmp_path: Path):
    proc, report = run_agent(tmp_path, "--apply", "--adapter", "cli")
    assert proc.returncode == 0, proc.stderr
    assert report["ok"] is True
    assert report["status"] == "installed"
    assert report["verification"]["ok"] is True
    assert len(report["verification"]["results"]) == 2
    for name in ("psup", "psup-mcp", "psupd"):
        assert (tmp_path / ".local" / "bin" / name).is_symlink()

    proc, report = run_agent(tmp_path, "--uninstall", "--adapter", "cli")
    assert proc.returncode == 0, proc.stderr
    assert report["ok"] is True
    assert report["status"] == "uninstalled"
    assert not (tmp_path / ".local" / "bin" / "psup").exists()


def test_unknown_adapter_fails_without_changes(tmp_path: Path):
    proc, report = run_agent(tmp_path, "--plan", "--adapter", "unknown")
    assert proc.returncode == 2
    assert report["ok"] is False
    assert report["status"] == "contract-error"
    assert "未知适配器" in report["error"]
    assert not (tmp_path / ".local").exists()


def test_verify_does_not_fallback_to_source_checkout(tmp_path: Path):
    proc, report = run_agent(tmp_path, "--verify", "--adapter", "cli")
    assert proc.returncode == 1
    assert report["ok"] is False
    assert report["status"] == "failed"
    assert "没有 psup" in report["verification"]["error"]


def test_host_install_requires_real_adapter_state(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "case \"$1 $2\" in\n"
        "  '--version ') echo 'codex-cli 0.167.2'; exit 0;;\n"
        "  'plugin marketplace') exit 0;;\n"
        "  'plugin list') echo 'PLUGIN STATUS'; exit 0;;\n"
        "  'plugin add') exit 0;;\n"
        "  'plugin remove') exit 0;;\n"
        "esac\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    env = dict(os.environ, HOME=str(tmp_path), PATH=f"{bin_dir}:/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--apply", "--adapter", "codex"],
        capture_output=True,
        text=True,
        env=env,
    )
    report = json.loads(proc.stdout)
    assert proc.returncode == 1
    assert report["ok"] is False
    assert report["status"] == "failed"
    codex_state = next(row for row in report["verification"]["adapters"] if row["id"] == "codex")
    assert codex_state["ok"] is False


def test_incompatible_agent_version_is_rejected(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text("#!/bin/sh\necho 'codex-cli 0.100.0'\n", encoding="utf-8")
    codex.chmod(0o755)
    env = dict(os.environ, HOME=str(tmp_path), PATH=f"{bin_dir}:/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--plan", "--adapter", "codex"],
        capture_output=True,
        text=True,
        env=env,
    )
    report = json.loads(proc.stdout)
    assert proc.returncode == 2
    assert report["ok"] is False
    assert "版本不兼容" in report["error"]


def test_copilot_adapter_self_installs_skill_and_mcp(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    copilot = bin_dir / "copilot"
    copilot.write_text(
        "#!/bin/sh\n"
        "case \"$1 $2\" in\n"
        "  '--version ') echo '1.0.107'; exit 0;;\n"
        "  'skill list')\n"
        "    test -f \"$HOME/skill\" && echo '[{\"name\":\"skynet-prompt\",\"enabled\":true}]' || echo '[]';;\n"
        "  'skill add') touch \"$HOME/skill\"; exit 0;;\n"
        "  'mcp list')\n"
        "    test -f \"$HOME/mcp\" && echo '{\"mcpServers\":{\"skynet-prompt\":{}}}' || echo '{\"mcpServers\":{}}';;\n"
        "  'mcp add') touch \"$HOME/mcp\"; exit 0;;\n"
        "  'config extensions.mode') echo 'load_only'; exit 0;;\n"
        "esac\n",
        encoding="utf-8",
    )
    copilot.chmod(0o755)
    env = dict(os.environ, HOME=str(tmp_path), PATH=f"{bin_dir}:/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--apply", "--adapter", "copilot"],
        capture_output=True,
        text=True,
        env=env,
    )
    report = json.loads(proc.stdout)
    assert proc.returncode == 0, proc.stderr
    assert report["ok"] is True
    assert report["status"] == "installed"
    copilot_state = next(
        row for row in report["verification"]["adapters"] if row["id"] == "copilot"
    )
    assert copilot_state["ok"] is True


def test_version_mismatch_is_rejected(tmp_path: Path):
    manifest = json.loads((ROOT / "install-manifest.json").read_text(encoding="utf-8"))
    manifest["version"] = "9.9.9"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    proc, report = run_agent(tmp_path, "--plan", "--manifest", str(path))
    assert proc.returncode == 2
    assert report["ok"] is False
    assert "版本" in report["error"]


def test_install_args_cannot_inject_installer_flags(tmp_path: Path):
    manifest = json.loads((ROOT / "install-manifest.json").read_text(encoding="utf-8"))
    manifest["adapters"][1]["install_args"] = ["--uninstall"]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    proc, report = run_agent(tmp_path, "--plan", "--manifest", str(path))
    assert proc.returncode == 2
    assert report["ok"] is False
    assert "install_args" in report["error"]


def test_invalid_manifest_signature_is_rejected(tmp_path: Path):
    manifest = json.loads((ROOT / "install-manifest.json").read_text(encoding="utf-8"))
    manifest["signature"] = {
        "algorithm": "ed25519",
        "key_id": "bad",
        "public_key_pem": "not-a-key",
        "value": "not-a-signature",
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    proc, report = run_agent(tmp_path, "--plan", "--manifest", str(path))
    assert proc.returncode == 2
    assert report["ok"] is False
    assert "签名无效" in report["error"]


def test_contract_hash_mismatch_is_rejected(tmp_path: Path):
    manifest = json.loads((ROOT / "install-manifest.json").read_text(encoding="utf-8"))
    manifest["contract"] = {"path": "AGENT_INSTALL.md", "sha256": "0" * 64}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    proc, report = run_agent(tmp_path, "--plan", "--manifest", str(path))
    assert proc.returncode == 2
    assert report["ok"] is False
    assert "哈希与 manifest 不一致" in report["error"]


def test_trust_store_verifies_signed_manifest_identity(tmp_path: Path):
    key = tmp_path / "ed25519.pem"
    generated = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
        capture_output=True,
    )
    assert generated.returncode == 0, generated.stderr
    trust = tmp_path / "trust" / "keys.json"
    trust.parent.mkdir()
    public = trust.parent / "ed25519.pub.pem"
    exported = subprocess.run(
        ["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(public)],
        capture_output=True,
    )
    assert exported.returncode == 0, exported.stderr

    from skynet_prompt.signing import sign_manifest

    manifest = json.loads((ROOT / "install-manifest.json").read_text(encoding="utf-8"))
    manifest = sign_manifest(manifest, key, key_id="agent-test")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    trust.write_text('{"schema_version":1,"keys":[]}', encoding="utf-8")
    add_key(trust, public, key_id="agent-test", publisher="test", status="dev")

    proc, report = run_agent(
        tmp_path,
        "--plan",
        "--manifest",
        str(manifest_path),
        "--trust",
        str(trust),
    )
    assert proc.returncode == 0, proc.stderr
    assert report["ok"] is True
    assert report["signature"] == {
        "present": True,
        "verified": True,
        "trusted": True,
        "key_id": "agent-test",
    }
