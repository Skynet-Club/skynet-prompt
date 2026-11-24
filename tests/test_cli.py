"""CLI 黑盒：JSON、退出码和原样输出。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "psup"), *args],
        capture_output=True, text=True,
    )


def test_selftest():
    proc = run("selftest")
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["count"] == 42
    assert result["official_count"] == 22
    assert result["sha256"] == result["meta_sha256"]


def test_list_and_print():
    listed = run("list", "--json")
    assert listed.returncode == 0, listed.stderr
    rows = json.loads(listed.stdout)
    assert len(rows) == 42
    item = rows[0]
    printed = run("print", item["id"])
    assert printed.returncode == 0, printed.stderr
    assert printed.stdout.rstrip("\n") == item["zh"]


def test_categories_and_audit():
    categories = run("categories", "--json")
    assert categories.returncode == 0, categories.stderr
    assert len(json.loads(categories.stdout)) == 9
    audit = run("audit", "--json")
    assert audit.returncode == 0, audit.stderr
    assert json.loads(audit.stdout)["official_ready"] is True


def test_doctor():
    proc = run("doctor")
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["count"] == 42
