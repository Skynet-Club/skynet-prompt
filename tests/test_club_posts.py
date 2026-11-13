"""Club 发布批次格式测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from skynet_prompt.release import release

ROOT = Path(__file__).resolve().parent.parent


def test_club_post_batch(tmp: Path):
    release_dir = tmp / "release"
    release(ROOT, release_dir)
    out = tmp / "posts"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_club_posts.py"),
            "--release",
            str(release_dir),
            "--out",
            str(out),
            "--channel",
            "13",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    batch = json.loads((out / "batch.json").read_text(encoding="utf-8"))
    assert batch["channel"] == "13"
    assert batch["count"] == 34
    assert all(row["author"] and row["source"] and row["sha256"] for row in batch["posts"])
    sample = (out / "kp-verify-18.md").read_text(encoding="utf-8")
    assert "作者：Karpathy" in sample
    assert "来源：https://" in sample
    assert "版权：" in sample
