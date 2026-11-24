#!/usr/bin/env python3
"""统一测试入口：选带 prompt_toolkit 的解释器，跑 Python 测试。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pick_python() -> Path | None:
    for candidate in (ROOT / ".venv" / "bin" / "python", Path(sys.executable)):
        if candidate.exists():
            probe = subprocess.run(
                [str(candidate), "-c", "import prompt_toolkit"],
                capture_output=True,
            )
            if probe.returncode == 0:
                return candidate
    return None


def main() -> int:
    python = pick_python()
    if python is None:
        print("找不到带 prompt_toolkit 的解释器；创建 .venv 后重试。", file=sys.stderr)
        return 2
    print(f"测试解释器：{python}")
    result = subprocess.run([str(python), str(ROOT / "tests" / "run.py")], cwd=ROOT)
    if result.returncode != 0:
        return result.returncode
    print("\nTEST GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
