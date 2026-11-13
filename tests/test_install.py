"""安装器的无宿主路径：只链三个命令，不碰 Hermes。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_no_hermes_install_links_commands(tmp_path: Path):
    env = dict(os.environ, HOME=str(tmp_path), PATH="/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--no-hermes"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    for name in ("psup", "psup-mcp", "psupd"):
        target = tmp_path / ".local" / "bin" / name
        assert target.is_symlink()
        assert target.resolve() == ROOT / name


def test_opencode_install_configures_plugin(tmp_path: Path):
    config = tmp_path / ".config" / "opencode" / "cli.json"
    config.parent.mkdir(parents=True)
    config.write_text('{"plugins": []}\n', encoding="utf-8")

    env = dict(os.environ, HOME=str(tmp_path), PATH="/usr/bin:/bin")
    install = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "opencode"],
        capture_output=True, text=True, env=env,
    )
    assert install.returncode == 0, install.stderr

    plugin = str(ROOT / "adapters" / "opencode-plugin")
    assert plugin in json.loads(config.read_text())["plugins"]
    commands = tmp_path / ".config" / "opencode" / "command"
    assert not list(commands.glob("psup*.md"))

    uninstall = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--uninstall", "opencode"],
        capture_output=True, text=True, env=env,
    )
    assert uninstall.returncode == 0, uninstall.stderr
    assert plugin not in json.loads(config.read_text())["plugins"]
    assert not list(commands.glob("psup*.md"))


def test_codex_shim_is_installed_and_reversible(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "codex-real"
    fake.write_text(
        "#!/bin/sh\n"
        "case \"$1 $2\" in\n"
        "  'plugin marketplace') exit 0;;\n"
        "  'plugin list') echo 'PLUGIN STATUS'; exit 0;;\n"
        "  'plugin add') exit 0;;\n"
        "  'plugin remove') exit 0;;\n"
        "esac\n"
        "echo 'codex-cli 0.167.0'\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    (bin_dir / "codex").symlink_to(fake)

    env = dict(os.environ, HOME=str(tmp_path), PATH=f"{bin_dir}:/usr/bin:/bin")
    install = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--with-picker", "codex"],
        capture_output=True, text=True, env=env,
    )
    assert install.returncode == 0, install.stderr

    shim = bin_dir / "codex"
    assert shim.is_file() and "skynet-prompt codex shim" in shim.read_text()
    assert (bin_dir / "codex.real").is_symlink()
    version = subprocess.run([str(shim), "--version"], capture_output=True, text=True, env=env)
    assert "codex-cli" in version.stdout

    uninstall = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--uninstall", "codex"],
        capture_output=True, text=True, env=env,
    )
    assert uninstall.returncode == 0, uninstall.stderr
    assert shim.is_symlink()
    assert shim.resolve() == fake
    assert not (bin_dir / "codex.real").exists()


def test_list_json_is_machine_readable(tmp_path: Path):
    env = dict(os.environ, HOME=str(tmp_path), PATH="/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--list", "--json"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["schema_version"] == 1
    assert {row["id"] for row in report["hosts"]} == {
        "codex", "pi", "opencode", "hermes", "copilot", "claude",
    }
    assert all(row["available"] is False for row in report["hosts"])


def test_copilot_install_registers_skill_and_mcp(tmp_path: Path):
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
        "  'skill remove') rm -f \"$HOME/skill\"; exit 0;;\n"
        "  'mcp list')\n"
        "    test -f \"$HOME/mcp\" && echo '{\"mcpServers\":{\"skynet-prompt\":{}}}' || echo '{\"mcpServers\":{}}';;\n"
        "  'mcp add') touch \"$HOME/mcp\"; exit 0;;\n"
        "  'mcp remove') rm -f \"$HOME/mcp\"; exit 0;;\n"
        "  'config extensions.mode') echo 'load_only'; exit 0;;\n"
        "esac\n",
        encoding="utf-8",
    )
    copilot.chmod(0o755)
    env = dict(os.environ, HOME=str(tmp_path), PATH=f"{bin_dir}:/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "copilot"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "skill").exists()
    assert (tmp_path / "mcp").exists()
    assert (tmp_path / ".copilot" / "extensions" / "skynet-prompt" / "extension.mjs").is_file()
    listed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--list", "--json"],
        capture_output=True,
        text=True,
        env=env,
    )
    row = next(row for row in json.loads(listed.stdout)["hosts"] if row["id"] == "copilot")
    assert row["installed"] is True
    assert row["skill"] is True
    assert row["mcp"] is True
    assert row["extension"] is True

    removed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--uninstall", "copilot"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert removed.returncode == 0, removed.stderr
    assert not (tmp_path / "skill").exists()
    assert not (tmp_path / "mcp").exists()
    assert not (tmp_path / ".copilot" / "extensions" / "skynet-prompt").exists()


def test_claude_install_registers_skill_hook_and_mcp(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude = bin_dir / "claude"
    claude.write_text(
        "#!/bin/sh\n"
        "case \"$1 $2\" in\n"
        "  '--version ') echo '2.1.314 (Claude Code)'; exit 0;;\n"
        "  'mcp get') test -f \"$HOME/mcp\"; exit $?;;\n"
        "  'mcp add') touch \"$HOME/mcp\"; exit 0;;\n"
        "  'mcp remove') rm -f \"$HOME/mcp\"; exit 0;;\n"
        "esac\n",
        encoding="utf-8",
    )
    claude.chmod(0o755)
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({
        "hooks": {
            "UserPromptSubmit": [
                {"matcher": "*", "hooks": [{"type": "command", "command": "echo keep"}]},
            ],
        },
        "permissions": {"allow": ["mcp__pencil"]},
    }), encoding="utf-8")
    env = dict(os.environ, HOME=str(tmp_path), PATH=f"{bin_dir}:/usr/bin:/bin")
    installed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "claude"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert installed.returncode == 0, installed.stderr
    assert (tmp_path / ".claude" / "skills" / "skynet-prompt" / "SKILL.md").is_file()
    assert (tmp_path / ".claude" / "skynet-prompt" / "hook.py").is_file()
    data = json.loads(settings.read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for group in data["hooks"]["UserPromptSubmit"]
        for hook in group["hooks"]
    ]
    assert "echo keep" in commands
    assert any("skynet-prompt/hook.py" in command for command in commands)
    assert data["permissions"] == {"allow": ["mcp__pencil"]}

    listed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--list", "--json"],
        capture_output=True,
        text=True,
        env=env,
    )
    row = next(row for row in json.loads(listed.stdout)["hosts"] if row["id"] == "claude")
    assert row["installed"] is True
    assert row["skill"] is True
    assert row["hook"] is True
    assert row["mcp"] is True

    removed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--uninstall", "claude"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert removed.returncode == 0, removed.stderr
    data = json.loads(settings.read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for group in data["hooks"]["UserPromptSubmit"]
        for hook in group["hooks"]
    ]
    assert commands == ["echo keep"]


def test_claude_trigger_hook_returns_context():
    hook = ROOT / "adapters" / "claude" / "skynet-prompt" / "hook.py"
    triggered = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps({"prompt": "；；定验收"}),
        capture_output=True,
        text=True,
    )
    assert triggered.returncode == 0
    output = json.loads(triggered.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "UserPromptSubmit"
    assert "定验收" in output["additionalContext"]
    assert "prompt_search" in output["additionalContext"]

    ordinary = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps({"prompt": "普通消息"}),
        capture_output=True,
        text=True,
    )
    assert ordinary.returncode == 0
    assert ordinary.stdout == ""
