"""评测任务集格式测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_evaluation_set_is_valid():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_evaluations.py")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["count"] >= 10


def test_evaluation_prompts_are_official():
    payload = json.loads(
        (ROOT / "evaluations" / "tasks.json").read_text(encoding="utf-8")
    )
    assert len({row["prompt_id"] for row in payload["tasks"]}) >= 8
