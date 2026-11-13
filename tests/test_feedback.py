"""本地反馈存储测试。"""

from __future__ import annotations

from pathlib import Path

from skynet_prompt.feedback import FeedbackError, add, load, summarize


def test_feedback_is_local_append_only(tmp: Path):
    path = tmp / "feedback.jsonl"
    add(path, item_id="kp-verify-18", kind="useful")
    add(path, item_id="kp-verify-18", kind="adopted")
    rows = load(path)
    assert len(rows) == 2
    assert rows[0]["kind"] == "useful"

    summary = summarize(path)
    assert summary["count"] == 2
    assert summary["by_kind"] == {"adopted": 1, "useful": 1}
    assert summary["by_item"][0] == {"id": "kp-verify-18", "count": 2}


def test_unknown_feedback_kind_fails(tmp: Path):
    try:
        add(tmp / "feedback.jsonl", item_id="kp-verify-18", kind="telemetry")
    except FeedbackError as exc:
        assert "未知反馈类型" in str(exc)
    else:
        raise AssertionError("未知反馈类型应失败")
