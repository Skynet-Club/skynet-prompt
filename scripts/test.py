#!/usr/bin/env python3
"""统一测试入口：选择带 prompt_toolkit 的解释器并跑完整测试。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def supports_prompt_toolkit(python: Path) -> bool:
    if not python.exists():
        return False
    proc = subprocess.run(
        [str(python), "-c", "import prompt_toolkit"],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def pick_python() -> Path | None:
    explicit = os.environ.get("SKYNET_PROMPT_TEST_PYTHON")
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend([
        ROOT / ".venv" / "bin" / "python",
        ROOT / ".venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    ])
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if supports_prompt_toolkit(candidate):
            return candidate
    return None


def run(python: Path, script: str) -> int:
    print(f"\n== {script} ==", flush=True)
    return subprocess.run([str(python), script], cwd=ROOT).returncode


def main() -> int:
    python = pick_python()
    if python is None:
        print(
            "找不到带 prompt_toolkit 的测试解释器。\n"
            "请创建 .venv 并安装依赖：\n"
            "  python3 -m venv .venv\n"
            "  .venv/bin/pip install -r requirements-test.txt\n"
            "或设置 SKYNET_PROMPT_TEST_PYTHON=<python 路径>。",
            file=sys.stderr,
        )
        return 2

    print(f"测试解释器：{python}")
    for script in ("tests/run.py", "tests/test_session.py"):
        code = run(python, script)
        if code != 0:
            print(f"\n测试失败：{script}（exit {code}）", file=sys.stderr)
            return code
    node = subprocess.run(
        [
            "node", "--test",
            "adapters/opencode-plugin/test/picker.test.mjs",
            "adapters/copilot/extension/test/rewrite.test.mjs",
        ],
        cwd=ROOT,
    )
    if node.returncode != 0:
        print("\n测试失败：宿主插件", file=sys.stderr)
        return node.returncode
    print("\nTEST GATE PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
