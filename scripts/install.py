"""安装 skynet-prompt 的命令行与各宿主集成。

    ./install.sh                  # 检测本机宿主并安装
    ./install.sh codex pi         # 只装指定宿主
    ./install.sh --list
    ./install.sh --uninstall codex

宿主集成都是可回滚的：codex 会把原来的软链备份成 codex.real，
卸载时恢复；opencode 只动 psup*.md 和 cli.json 里的插件项；Hermes 修改前有备份。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKUP = Path.home() / ".hermes" / "cache" / "skynet-prompt-backup"
CODEX_MARKER = "# skynet-prompt codex shim"
HOSTS = ("codex", "pi", "opencode", "hermes", "copilot", "claude")

ANCHOR_BEFORE = """        _completer = cli_slash_completer(self)
        input_area = TextArea(
"""
ANCHOR_AFTER = f"""        _completer = cli_slash_completer(self)
        # 提示词补充：;; 抽屉。装在宿主外，导入失败就当没装，不影响原补全。
        _input_completer = _completer
        try:
            from prompt_toolkit.completion import merge_completers
            try:
                from skynet_prompt.menu import get_completer as _get_prompt_menu
            except ImportError:
                import sys as _sys
                _sys.path.append("{REPO}")
                from skynet_prompt.menu import get_completer as _get_prompt_menu
            _prompt_menu = _get_prompt_menu()
            if _prompt_menu is not None:
                _input_completer = merge_completers([_completer, _prompt_menu])
        except Exception:
            pass
        input_area = TextArea(
"""
OLD_LINE = "            completer=ThreadedCompleter(_completer),\n"
NEW_LINE = "            completer=ThreadedCompleter(_input_completer),\n"

DRAWER_BEFORE = """        from hermes_cli.cli_subagent_monitor import install_dock
        install_dock(self)
"""
DRAWER_AFTER = f"""        from hermes_cli.cli_subagent_monitor import install_dock
        install_dock(self)
        # 提示词补充：;; 抽屉（左列类目 / 右列条目+预览）。装在宿主外，导入失败就当没装。
        try:
            try:
                from skynet_prompt.drawer import install as _install_drawer
            except ImportError:
                import sys as _sys
                _sys.path.append("{REPO}")
                from skynet_prompt.drawer import install as _install_drawer
            _install_drawer(self)
        except Exception:
            pass
"""


def say(text: str) -> None:
    print(text, flush=True)


def run(command: list[str], dry: bool = False) -> subprocess.CompletedProcess:
    if dry:
        say("  · " + " ".join(shlex.quote(part) for part in command))
        return subprocess.CompletedProcess(command, 0, "", "")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        say(f"  ! {' '.join(command[:3])} 失败：{detail[-1] if detail else '未知错误'}")
    return result


def link_command(name: str, dry: bool = False) -> str:
    target = Path.home() / ".local" / "bin" / name
    source = REPO / name
    if target.is_symlink() and target.resolve() == source.resolve():
        return f"  ✓ {name} 已就位"
    if target.exists() and not target.is_symlink():
        return f"  ! {target} 已存在且不是软链，没动它"
    if not dry:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.unlink(missing_ok=True)
        target.symlink_to(source)
    return f"  ✓ {name} → {target}"


def unlink_command(name: str, dry: bool = False) -> str:
    target = Path.home() / ".local" / "bin" / name
    if target.is_symlink() and target.resolve() == (REPO / name).resolve():
        if not dry:
            target.unlink()
        return f"  ✓ 移除 {target}"
    return f"  · {target} 不是本项目的软链，跳过"


def detect_hermes() -> tuple[Path | None, Path | None]:
    exe = shutil.which("hermes")
    if not exe:
        return None, None
    try:
        out = subprocess.run([exe, "--print-runtime-command"],
                             capture_output=True, text=True, timeout=60)
        argv = json.loads(out.stdout)
    except Exception:
        return None, None
    python = Path(argv[0]) if argv else None
    match = re.search(r"sys\.path\.insert\(0,\s*'([^']+)'", " ".join(str(a) for a in argv))
    root = Path(match.group(1)) if match else None
    if not root or not (root / "hermes_cli").is_dir():
        return None, python
    return root, python


def patch_host(host: Path) -> str:
    src = host.read_text()
    if "_input_completer" in src:
        return f"  · 补全器已挂过，跳过（{host}）"
    if ANCHOR_BEFORE not in src or OLD_LINE not in src:
        raise SystemExit(f"锚点没找到，宿主版本变了，手工看一眼：{host}")
    BACKUP.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(host, BACKUP / f"cli_tui_mixin.py.{stamp}")
    out = src.replace(ANCHOR_BEFORE, ANCHOR_AFTER, 1).replace(OLD_LINE, NEW_LINE, 1)
    host.write_text(out)
    return f"  ✓ 补全器已挂：{host}（备份 {BACKUP}/cli_tui_mixin.py.{stamp}）"


def patch_drawer(host: Path) -> str:
    src = host.read_text()
    if "_install_drawer" in src:
        return "  · 抽屉已挂过，跳过"
    if DRAWER_BEFORE not in src:
        raise SystemExit("抽屉锚点没找到，宿主版本变了")
    host.write_text(src.replace(DRAWER_BEFORE, DRAWER_AFTER, 1))
    return "  ✓ 抽屉已挂进 _tui_build_layout"


def codex_plugin_state(codex: str) -> tuple[bool, bool]:
    try:
        market = subprocess.run([codex, "plugin", "marketplace", "list"],
                                capture_output=True, text=True).stdout
        plugins = subprocess.run([codex, "plugin", "list"],
                                 capture_output=True, text=True).stdout
    except Exception:
        return False, False
    return "skynet-prompt" in market, "skynet-prompt@skynet-prompt" in plugins


def codex_shim_path() -> Path:
    codex = shutil.which("codex")
    return Path(codex) if codex else Path.home() / ".local" / "bin" / "codex"


def install_codex(dry: bool = False, with_picker: bool = False) -> None:
    codex = shutil.which("codex")
    if not codex:
        say("  · 没找到 codex，跳过")
        return

    has_market, has_plugin = codex_plugin_state(codex)
    if not has_market:
        result = run([codex, "plugin", "marketplace", "add", str(REPO)], dry)
        if result.returncode == 0:
            say("  ✓ codex 插件市场已添加")
    else:
        say("  · codex 插件市场已存在")
    if not has_plugin:
        result = run([codex, "plugin", "add", "skynet-prompt@skynet-prompt"], dry)
        if result.returncode == 0:
            say("  ✓ codex 插件已安装（42 条 + ；； 索引技能）")
    else:
        say("  · codex 插件已安装")

    if not with_picker:
        say("  · 默认不装 Ctrl+G picker；需要时加 --with-picker")
        return

    shim = codex_shim_path()
    real = shim.with_name("codex.real")
    picker = REPO / "adapters" / "codex-picker" / "psup-editor.sh"

    if shim.is_symlink():
        target = shim.resolve()
        if real.is_symlink():
            if real.resolve() != target and not dry:
                real.unlink()
                real.symlink_to(target)
        elif real.exists():
            say(f"  ! {real} 已存在且不是软链，跳过 codex shim")
            return
        elif not dry:
            real.symlink_to(target)
        if not dry:
            shim.unlink()
    elif shim.exists():
        if CODEX_MARKER not in shim.read_text(errors="ignore"):
            say("  ! codex 不是软链，跳过 shim；可改用 codex-prompt")
            return
    else:
        say("  ! 找不到 codex 可执行文件，跳过 shim")
        return

    wrapper = f"""#!/bin/sh
{CODEX_MARKER}
if [ -x {shlex.quote(str(picker))} ]; then
  PSUP_ORIGINAL_VISUAL="${{VISUAL:-${{EDITOR:-}}}}" VISUAL={shlex.quote(str(picker))} exec {shlex.quote(str(real))} "$@"
fi
exec {shlex.quote(str(real))} "$@"
"""
    if dry:
        say(f"  · 写入 {shim}（设置 $VISUAL，原文件备份为 {real}）")
    else:
        shim.write_text(wrapper)
        shim.chmod(0o755)
        say(f"  ✓ codex Ctrl+G 抽屉已接入（原文件：{real}）")


def uninstall_codex(dry: bool = False) -> None:
    codex = shutil.which("codex")
    if codex:
        run([codex, "plugin", "remove", "skynet-prompt@skynet-prompt"], dry)
        run([codex, "plugin", "marketplace", "remove", "skynet-prompt"], dry)

    shim = codex_shim_path()
    real = shim.with_name("codex.real")
    if shim.exists() and shim.is_file() and CODEX_MARKER in shim.read_text(errors="ignore"):
        if real.is_symlink():
            target = os.readlink(real)
            if not dry:
                shim.unlink()
                shim.symlink_to(target)
                real.unlink()
            say(f"  ✓ codex 已恢复为 {target}")
        elif not dry:
            shim.unlink()
            say("  ✓ codex shim 已移除")
    else:
        say("  · 没有发现 codex shim，跳过")


def install_pi(dry: bool = False) -> None:
    pi = shutil.which("pi")
    if not pi:
        say("  · 没找到 pi，跳过")
        return
    result = run([pi, "install", str(REPO)], dry)
    if result.returncode == 0:
        say("  ✓ pi 包已安装（；； 抽屉 + 42 个 /psup-*）")


def uninstall_pi(dry: bool = False) -> None:
    pi = shutil.which("pi")
    if pi:
        run([pi, "remove", str(REPO)], dry)
        say("  ✓ pi 包已移除")


def opencode_commands() -> tuple[Path, Path]:
    return REPO / "adapters" / "opencode" / "commands", Path.home() / ".config" / "opencode" / "command"


def opencode_cli_config() -> Path:
    return Path.home() / ".config" / "opencode" / "cli.json"


def opencode_plugin_path() -> str:
    return str(REPO / "adapters" / "opencode-plugin")


def opencode_plugin_configured() -> bool:
    path = opencode_cli_config()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return opencode_plugin_path() in (data.get("plugins") or [])


def configure_opencode_plugin(dry: bool = False) -> None:
    path = opencode_cli_config()
    if not path.exists():
        say("  · 没有 ~/.config/opencode/cli.json，跳过插件配置")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        say(f"  ! 读不了 {path}：{exc}")
        return
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        say(f"  ! {path} 里的 plugins 不是数组，没动它")
        return
    plugin = opencode_plugin_path()
    if plugin in plugins:
        say("  · opencode 插件已配置")
        return
    if dry:
        say(f"  · 将把插件加入 {path}")
        return
    backup = path.with_name(path.name + ".bak-skynet-prompt")
    shutil.copy2(path, backup)
    plugins.append(plugin)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say(f"  ✓ opencode 插件已加入 {path}（备份 {backup}）")


def install_opencode(dry: bool = False, with_commands: bool = False) -> None:
    src, dst = opencode_commands()
    files = sorted(src.glob("psup-*.md"))
    if with_commands:
        if dry:
            say(f"  · 复制 {len(files)} 个直接命令到 {dst}")
        else:
            dst.mkdir(parents=True, exist_ok=True)
            for path in files:
                shutil.copy2(path, dst / path.name)
            say(f"  ✓ opencode 直接命令 {len(files)} 个 → {dst}")
    else:
        removed = 0
        if dst.is_dir():
            wanted = {path.name for path in files}
            for path in dst.glob("psup-*.md"):
                if path.name in wanted:
                    if not dry:
                        path.unlink()
                    removed += 1
            legacy = dst / "psup.md"
            if legacy.exists() and "skynet-prompt" in legacy.read_text(errors="ignore"):
                if not dry:
                    legacy.unlink()
                removed += 1
        say(f"  ✓ 清理 {removed} 个旧命令（/psup 交给插件选择器）")
    configure_opencode_plugin(dry)


def uninstall_opencode(dry: bool = False) -> None:
    src, dst = opencode_commands()
    expected = {path.name for path in src.glob("psup-*.md")}
    expected.add("psup.md")
    removed = 0
    for path in dst.glob("psup*.md"):
        if path.name in expected:
            if not dry:
                path.unlink()
            removed += 1
    say(f"  ✓ 移除 {removed} 个 opencode 命令")

    path = opencode_cli_config()
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return
    plugin = opencode_plugin_path()
    if plugin not in plugins:
        return
    if not dry:
        backup = path.with_name(path.name + ".bak-skynet-prompt")
        shutil.copy2(path, backup)
        data["plugins"] = [item for item in plugins if item != plugin]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say(f"  ✓ 从 {path} 移除 opencode 插件")


def install_hermes(dry: bool = False) -> None:
    root, _python = detect_hermes()
    if root is None:
        say("  · 没找到 Hermes，跳过")
        return
    host = root / "hermes_cli" / "cli_tui_mixin.py"
    if not host.exists():
        say(f"  · 宿主里没有 {host}，跳过")
        return
    if dry:
        say(f"  · 修改 {host}（补全器 + 抽屉）")
        return
    say(patch_host(host))
    say(patch_drawer(host))


def uninstall_hermes(dry: bool = False) -> None:
    say(f"  · Hermes 补丁不自动回滚；备份在 {BACKUP}")


def copilot_extension_dir() -> Path:
    return Path.home() / ".copilot" / "extensions" / "skynet-prompt"


def copilot_state(copilot: str) -> tuple[bool, bool, bool]:
    skills = subprocess.run(
        [copilot, "skill", "list", "--json"],
        capture_output=True,
        text=True,
    )
    mcp = subprocess.run(
        [copilot, "mcp", "list", "--json"],
        capture_output=True,
        text=True,
    )
    try:
        skill_rows = json.loads(skills.stdout) if skills.returncode == 0 else []
        mcp_rows = json.loads(mcp.stdout).get("mcpServers", {}) if mcp.returncode == 0 else {}
    except (json.JSONDecodeError, AttributeError):
        return False, False, False
    has_skill = any(
        row.get("name") == "skynet-prompt" and row.get("enabled") is not False
        for row in skill_rows
    )
    extension = (copilot_extension_dir() / "extension.mjs").is_file()
    return has_skill, "skynet-prompt" in mcp_rows, extension


def install_copilot(dry: bool = False) -> None:
    copilot = shutil.which("copilot")
    if not copilot:
        say("  · 没找到 copilot，跳过")
        return
    skill = REPO / "adapters" / "copilot" / "psup" / "SKILL.md"
    if dry:
        say(f"  · {copilot} skill add {skill}")
        say(f"  · {copilot} mcp add skynet-prompt -- {Path.home() / '.local/bin/psup-mcp'}")
        say(f"  · {copilot} config extensions.mode load_only")
        return
    has_skill, has_mcp, has_extension = copilot_state(copilot)
    if has_skill:
        say("  · Copilot skill 已安装")
    else:
        result = run([copilot, "skill", "add", str(skill)])
        if result.returncode == 0:
            say("  ✓ Copilot skill 已安装")
    if has_mcp:
        say("  · Copilot MCP 已配置")
    else:
        result = run([
            copilot, "mcp", "add", "skynet-prompt", "--",
            str(Path.home() / ".local/bin/psup-mcp"),
        ])
        if result.returncode == 0:
            say("  ✓ Copilot MCP 已配置")
    source = REPO / "adapters" / "copilot" / "extension"
    target = copilot_extension_dir()
    target.mkdir(parents=True, exist_ok=True)
    changed = False
    for name in ("extension.mjs", "rewrite.mjs"):
        src = source / name
        dst = target / name
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copy2(src, dst)
            changed = True
    if changed:
        say(f"  ✓ Copilot 输入触发器已安装/更新：{target}")
    elif has_extension:
        say("  · Copilot 输入触发器已是最新")
    else:
        say(f"  ✓ Copilot 输入触发器已安装：{target}")
    mode = subprocess.run(
        [copilot, "config", "extensions.mode"],
        capture_output=True,
        text=True,
    )
    current = mode.stdout.strip()
    if mode.returncode == 0 and current in {"load_only", "load_and_augment"}:
        say(f"  · Copilot extensions.mode 已是 {current}")
    else:
        result = run([copilot, "config", "extensions.mode", "load_only"])
        if result.returncode == 0:
            say("  ✓ Copilot extensions.mode 已设为 load_only")


def uninstall_copilot(dry: bool = False) -> None:
    copilot = shutil.which("copilot")
    if not copilot:
        say("  · 没找到 copilot，跳过")
        return
    run([copilot, "skill", "remove", "skynet-prompt"], dry)
    run([copilot, "mcp", "remove", "skynet-prompt"], dry)
    target = copilot_extension_dir()
    if target.exists() and not dry:
        shutil.rmtree(target)
    say("  ✓ Copilot skill、MCP 和输入触发器已移除")


def claude_skill_dir() -> Path:
    return Path.home() / ".claude" / "skills" / "skynet-prompt"


def claude_hook_dir() -> Path:
    return Path.home() / ".claude" / "skynet-prompt"


def claude_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def claude_hook_command() -> str:
    return f"python3 {shlex.quote(str(claude_hook_dir() / 'hook.py'))}"


def claude_hook_present(settings: dict) -> bool:
    expected = claude_hook_command()
    groups = ((settings.get("hooks") or {}).get("UserPromptSubmit") or [])
    return any(
        hook.get("type") == "command" and hook.get("command") == expected
        for group in groups if isinstance(group, dict)
        for hook in (group.get("hooks") or []) if isinstance(hook, dict)
    )


def update_claude_hook(install: bool) -> None:
    path = claude_settings_path()
    if path.exists():
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"无法读取 Claude settings：{exc}") from exc
    else:
        settings = {}
    hooks = settings.setdefault("hooks", {})
    groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(groups, list):
        raise SystemExit("Claude hooks.UserPromptSubmit 不是数组，未修改")
    expected = claude_hook_command()
    kept = []
    for group in groups:
        if not isinstance(group, dict):
            kept.append(group)
            continue
        rows = [
            hook for hook in (group.get("hooks") or [])
            if not (isinstance(hook, dict) and hook.get("command") == expected)
        ]
        if rows:
            kept.append({**group, "hooks": rows})
    if install:
        kept.append({
            "matcher": "*",
            "hooks": [{"type": "command", "command": expected}],
        })
    if kept:
        hooks["UserPromptSubmit"] = kept
    else:
        hooks.pop("UserPromptSubmit", None)
    if not hooks:
        settings.pop("hooks", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = Path.home() / ".claude" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(path, backup_dir / f"settings.json.skynet-prompt-{stamp}")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(settings, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def claude_state(claude: str) -> tuple[bool, bool, bool]:
    skill = (claude_skill_dir() / "SKILL.md").is_file()
    hook_file = (claude_hook_dir() / "hook.py").is_file()
    try:
        settings = json.loads(claude_settings_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        settings = {}
    hook = hook_file and claude_hook_present(settings)
    mcp = subprocess.run(
        [claude, "mcp", "get", "skynet-prompt"],
        capture_output=True,
        text=True,
    ).returncode == 0
    return skill, hook, mcp


def install_claude(dry: bool = False) -> None:
    claude = shutil.which("claude")
    if not claude:
        say("  · 没找到 claude，跳过")
        return
    source = REPO / "adapters" / "claude" / "skynet-prompt"
    mcp_command = Path.home() / ".local/bin/psup-mcp"
    if dry:
        say(f"  · 复制 Claude Skill 到 {claude_skill_dir()}")
        say(f"  · 安装 UserPromptSubmit Hook 到 {claude_hook_dir()}")
        say(f"  · {claude} mcp add --scope user skynet-prompt {mcp_command}")
        return
    skill_dir = claude_skill_dir()
    hook_dir = claude_hook_dir()
    skill_dir.mkdir(parents=True, exist_ok=True)
    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "SKILL.md", skill_dir / "SKILL.md")
    shutil.copy2(source / "hook.py", hook_dir / "hook.py")
    (hook_dir / "hook.py").chmod(0o755)
    update_claude_hook(install=True)
    say("  ✓ Claude Skill 和 UserPromptSubmit Hook 已安装")
    has_skill, has_hook, has_mcp = claude_state(claude)
    if has_mcp:
        say("  · Claude MCP 已配置")
    else:
        result = run([
            claude, "mcp", "add", "--scope", "user",
            "skynet-prompt", str(mcp_command),
        ])
        if result.returncode == 0:
            say("  ✓ Claude MCP 已配置")


def uninstall_claude(dry: bool = False) -> None:
    claude = shutil.which("claude")
    if claude:
        run([claude, "mcp", "remove", "--scope", "user", "skynet-prompt"], dry)
    if not dry:
        update_claude_hook(install=False)
        shutil.rmtree(claude_skill_dir(), ignore_errors=True)
        shutil.rmtree(claude_hook_dir(), ignore_errors=True)
    say("  ✓ Claude Skill、MCP 和输入 Hook 已移除")


def detect_hosts() -> dict[str, str]:
    found: dict[str, str] = {}
    for name in ("codex", "pi", "opencode", "copilot", "claude"):
        path = shutil.which(name)
        if path:
            found[name] = path
    root, _ = detect_hermes()
    if root:
        found["hermes"] = str(root)
    return found


def list_state() -> dict:
    found = detect_hosts()
    rows = []
    for name in HOSTS:
        row = {
            "id": name,
            "available": name in found,
            "path": found.get(name),
            "installed": False,
            "state": "unavailable",
        }
        if name not in found:
            rows.append(row)
            continue
        if name == "codex":
            market, plugin = codex_plugin_state(found[name])
            shim = codex_shim_path().is_file() and CODEX_MARKER in codex_shim_path().read_text(errors="ignore")
            row.update(installed=plugin, state="installed" if plugin else "not-installed",
                       marketplace=market, picker_shim=shim)
        elif name == "pi":
            installed = REPO.name in subprocess.run(
                [found[name], "list"], capture_output=True, text=True
            ).stdout
            row.update(installed=installed, state="installed" if installed else "not-installed")
        elif name == "opencode":
            _, dst = opencode_commands()
            configured = opencode_plugin_configured()
            direct = len(list(dst.glob("psup-*.md")))
            row.update(installed=configured, state="installed" if configured else "not-installed",
                       direct_commands=direct)
        else:
            if name == "hermes":
                host = Path(found[name]) / "hermes_cli" / "cli_tui_mixin.py"
                mounted = host.read_text(errors="ignore").find("_install_drawer") >= 0
                row.update(installed=mounted, state="installed" if mounted else "not-installed")
            elif name == "copilot":
                has_skill, has_mcp, has_extension = copilot_state(found[name])
                installed = has_skill and has_mcp and has_extension
                row.update(installed=installed, state="installed" if installed else "not-installed",
                           skill=has_skill, mcp=has_mcp, extension=has_extension)
            else:
                has_skill, has_hook, has_mcp = claude_state(found[name])
                installed = has_skill and has_hook and has_mcp
                row.update(installed=installed, state="installed" if installed else "not-installed",
                           skill=has_skill, hook=has_hook, mcp=has_mcp)
        rows.append(row)
    return {
        "schema_version": 1,
        "product": "skynet-prompt",
        "hosts": rows,
    }


def show_list() -> None:
    state = list_state()
    available = [row for row in state["hosts"] if row["available"]]
    if not available:
        say("没有检测到宿主；psup 命令行仍可用。")
        return
    for row in available:
        detail = ""
        if row["id"] == "codex" and row.get("picker_shim"):
            detail = " · shim"
        elif row["id"] == "opencode" and row.get("direct_commands"):
            detail = f" · {row['direct_commands']} 个直接命令"
        label = "已安装" if row["installed"] else "未安装"
        say(f"  {row['id']:9} {label}{detail}")


def install_host(name: str, dry: bool, with_picker: bool = False, with_commands: bool = False) -> None:
    say(f"[{name}]")
    if name == "codex":
        install_codex(dry, with_picker)
    elif name == "opencode":
        install_opencode(dry, with_commands)
    elif name == "copilot":
        install_copilot(dry)
    elif name == "claude":
        install_claude(dry)
    else:
        {"pi": install_pi, "hermes": install_hermes}[name](dry)


def uninstall_host(name: str, dry: bool) -> None:
    say(f"[{name}]")
    {"codex": uninstall_codex, "pi": uninstall_pi, "opencode": uninstall_opencode,
     "hermes": uninstall_hermes, "copilot": uninstall_copilot,
     "claude": uninstall_claude}[name](dry)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="安装 skynet-prompt 与宿主集成")
    parser.add_argument(
        "hosts", nargs="*", choices=HOSTS,
        help="codex / pi / opencode / hermes / copilot / claude",
    )
    parser.add_argument("--host", action="append", default=[], choices=HOSTS)
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出 --list 状态")
    parser.add_argument("--cli-only", action="store_true", help="只链接 psup 命令，不安装任何宿主")
    parser.add_argument("--no-hermes", action="store_true", help="兼容旧参数：不装 Hermes")
    parser.add_argument("--with-picker", action="store_true", help="codex 额外安装 Ctrl+G 抽屉")
    parser.add_argument("--with-commands", action="store_true", help="opencode 额外复制 /psup-<id> 直接命令")
    args = parser.parse_args(argv)

    if args.list:
        if args.json:
            print(json.dumps(list_state(), ensure_ascii=False, indent=2))
        else:
            show_list()
        return 0

    selected = args.hosts + args.host
    if args.cli_only and selected:
        parser.error("--cli-only 不能和宿主参数同时使用")
    detected = detect_hosts()
    if args.cli_only:
        selected = []
    elif not selected:
        selected = [name for name in HOSTS if name in detected]
    if args.no_hermes:
        selected = [name for name in selected if name != "hermes"]

    say("skynet-prompt" + (" 卸载" if args.uninstall else " 安装"))
    if args.uninstall:
        for name in ("psup", "psup-mcp", "psupd"):
            say(unlink_command(name, args.dry_run))
        for name in selected:
            uninstall_host(name, args.dry_run)
        say("\n完成。")
        return 0

    for name in ("psup", "psup-mcp", "psupd"):
        say(link_command(name, args.dry_run))
    for name in selected:
        install_host(name, args.dry_run, args.with_picker, args.with_commands)

    say("\n完成。")
    if "codex" in selected:
        if args.with_picker:
            say("codex：输入 ；； 后按 Ctrl+G 打开抽屉。")
        else:
            say("codex：输入 ；； 开始浏览；兼容入口 $psup。")
    if "pi" in selected:
        say("pi：输入 ；； 打开抽屉；兼容入口 ;;。")
    if "opencode" in selected:
        say("opencode：当前输入插件使用 /prompts；暂不支持 ；； 原生拦截。")
    if "hermes" in selected:
        say("hermes：新开会话，输入 ；；。")
    if "copilot" in selected:
        say("copilot：重新打开会话，输入 ；；。")
    if "claude" in selected:
        say("claude：重新打开会话，输入 ；；。")
    if args.cli_only:
        say("仅命令行：psup / psup-mcp / psupd 已安装。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
