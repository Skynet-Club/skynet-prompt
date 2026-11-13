"""60 样本 cross-model 聚合结果测试。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_aggregate_evaluation_is_significant():
    data = json.loads(
        (ROOT / "evaluations" / "results-advisor-cross-model-60.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["total"] == 60
    assert data["wins"] == {"baseline": 11, "augmented": 38, "tie": 11}
    assert data["decisive_win_rate"] == 0.776
    assert data["sign_test_p_non_ties"] < 0.0001
