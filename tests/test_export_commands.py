"""opencode 命令壳必须调用 MCP，并提供全库入口。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_opencode_commands_use_mcp(tmp_path: Path):
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_commands.py"),
            "--target",
            "opencode",
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    browse = (tmp_path / "psup.md").read_text(encoding="utf-8")
    category = (tmp_path / "定验收.md").read_text(encoding="utf-8")
    assert "prompt_search" in browse
    assert "prompt_get" in category
    assert '"category":"定验收"' in category
    assert "命令文件" in (tmp_path / "README.md").read_text(encoding="utf-8")
