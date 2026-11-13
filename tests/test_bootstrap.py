"""一条命令安装入口的只读计划和临时 HOME 执行。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "bootstrap.py"


def run(home: Path, *args: str) -> tuple[subprocess.CompletedProcess, dict]:
    env = dict(os.environ, HOME=str(home), PATH="/usr/bin:/bin")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return proc, json.loads(proc.stdout)


def test_bootstrap_default_is_non_mutating(tmp_path: Path):
    proc, report = run(tmp_path, "--adapter", "cli")
    assert proc.returncode == 0, proc.stderr
    assert report["ok"] is True
    assert report["mode"] == "plan"
    assert report["selected"] == ["cli"]
    assert not (tmp_path / ".local").exists()


def test_bootstrap_apply_installs_cli(tmp_path: Path):
    proc, report = run(tmp_path, "--apply", "--adapter", "cli")
    assert proc.returncode == 0, proc.stderr
    assert report["ok"] is True
    assert report["mode"] == "apply"
    assert report["verification"]["ok"] is True
    assert (tmp_path / ".local" / "bin" / "psup").is_symlink()
