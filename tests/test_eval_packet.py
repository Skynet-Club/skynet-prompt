"""人工盲评包导出测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_eval_packet_is_blind_and_complete(tmp: Path):
    out = tmp / "packets"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_eval_packet.py"),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    key = json.loads((out / "answer-key.json").read_text(encoding="utf-8"))
    assert len(key) == 10
    assert all(set(row) == {"A", "B"} for row in key.values())
    packet = (out / "eval-plan-01.md").read_text(encoding="utf-8")
    assert "## 回答 A" in packet
    assert "## 回答 B" in packet
    assert "baseline" not in packet
    assert "augmented" not in packet
