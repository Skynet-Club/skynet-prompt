"""产品入口与宿主兼容性清单。"""

from __future__ import annotations

from .trigger import ASCII_TRIGGER, CANONICAL_TRIGGER, LITERAL_ESCAPE

SURFACES = [
    {
        "id": "cli",
        "name": "psup CLI",
        "level": "B",
        "status": "available",
        "capabilities": ["packs", "search", "get", "compose"],
    },
    {
        "id": "tui",
        "name": "psup fzf TUI",
        "level": "B",
        "status": "available",
        "capabilities": ["packs", "search", "get", "compose"],
    },
    {
        "id": "mcp",
        "name": "psup-mcp",
        "level": "B",
        "status": "available",
        "capabilities": ["packs", "search", "get", "compose"],
    },
    {
        "id": "http",
        "name": "psupd local API",
        "level": "B",
        "status": "available-loopback",
        "capabilities": ["packs", "search", "get", "compose", "audit"],
    },
    {
        "id": "web",
        "name": "Web UI",
        "level": "C",
        "status": "available-loopback",
        "capabilities": ["browse", "search", "compose", "copy"],
    },
    {
        "id": "hermes",
        "name": "Hermes drawer",
        "level": "A",
        "status": "verified",
        "supported_versions": ["0.22.5+3133.gc419cf7"],
        "capabilities": ["search", "get", "insert", "undo"],
        "tested_capabilities": ["packs", "search", "get", "compose"],
    },
    {
        "id": "codex",
        "name": "Codex shell",
        "level": "B",
        "status": "verified",
        "supported_versions": ["0.167.2"],
        "plugin_version": "0.3.0",
        "capabilities": ["packs", "search", "get", "compose"],
    },
    {
        "id": "claude-code",
        "name": "Claude Code shell",
        "level": "B",
        "status": "skill-hook-mcp-installed-mcp-health-blocked",
        "supported_versions": ["2.1.314"],
        "capabilities": ["packs", "search", "get", "compose", "skill", "hook", "mcp"],
    },
    {
        "id": "opencode",
        "name": "OpenCode shell + TUI plugin",
        "level": "B",
        "status": "shell-verified-tui-unverified",
        "supported_versions": ["2.2.7"],
        "capabilities": ["packs", "search", "get", "compose"],
        "experimental_capabilities": ["insert"],
    },
    {
        "id": "pi",
        "name": "pi shell + package",
        "level": "B",
        "status": "shell-verified-package-installed",
        "supported_versions": ["1.5.0"],
        "capabilities": ["packs", "search", "get", "compose"],
        "experimental_capabilities": ["insert", "undo"],
    },
    {
        "id": "copilot",
        "name": "Copilot CLI shell",
        "level": "B",
        "status": "skill-mcp-installed-auth-blocked",
        "supported_versions": ["1.0.107"],
        "capabilities": ["packs", "search", "get", "compose", "skill", "mcp"],
    },
    {
        "id": "dsh",
        "name": "DeepSeek Harness",
        "level": "B",
        "status": "headless-and-web-verified",
        "supported_versions": ["0.2.1-rc.5"],
        "capabilities": ["packs", "search", "get", "compose"],
        "web_status": "runner-loopback-auth-required",
    },
    {
        "id": "1agent",
        "name": "1Agent",
        "level": "B",
        "status": "terminal-tool-verified",
        "supported_versions": ["0.96.1"],
        "capabilities": ["packs", "search", "get", "compose"],
        "notes": "terminal_create/terminal_exec tested with deterministic provider; deepseek provider unsupported by this build",
    },
    {
        "id": "desktop-gui",
        "name": "Desktop GUI",
        "level": "D",
        "status": "planned",
        "capabilities": [],
    },
]


def capability_manifest() -> dict:
    return {
        "schema_version": 1,
        "product": "skynet-prompt",
        "platforms": {
            "supported": ["linux"],
            "verified": ["ubuntu"],
            "planned": ["windows", "macos"],
        },
        "experience": {
            "trigger": CANONICAL_TRIGGER,
            "aliases": [ASCII_TRIGGER],
            "literal_escape": LITERAL_ESCAPE,
            "native_interception": ["hermes", "pi"],
            "instruction_fallback": ["codex", "copilot", "claude-code", "mcp"],
            "command_fallback": ["cli", "http", "web"],
        },
        "surfaces": SURFACES,
    }
