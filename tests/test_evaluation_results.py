"""真实评测结果文件完整性测试。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_fixed_selection_results_are_recorded():
    data = json.loads(
        (ROOT / "evaluations" / "results-2026-11-13.json").read_text(encoding="utf-8")
    )
    assert data["ok"] is True
    assert data["selection"] == "fixed"
    assert data["count"] == 10
    assert data["wins"] == {"baseline": 5, "augmented": 4, "tie": 1}


def test_advisor_results_are_recorded():
    data = json.loads(
        (ROOT / "evaluations" / "results-advisor-2026-11-13.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["ok"] is True
    assert data["selection"] == "advisor"
    assert data["count"] == 10
    assert data["wins"] == {"baseline": 2, "augmented": 6, "tie": 2}
    assert all(row["selected_prompt_id"] for row in data["rows"])
