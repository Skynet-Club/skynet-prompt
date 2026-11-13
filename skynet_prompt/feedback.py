"""本地提示词反馈，不包含会话内容。"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

KINDS = {"adopted", "undone", "useful", "not-useful", "source-broken"}


class FeedbackError(ValueError):
    pass


def default_path() -> Path:
    return Path.home() / ".local" / "share" / "skynet-prompt" / "feedback.jsonl"


def add(path: Path, *, item_id: str, kind: str, note: str = "") -> dict:
    if kind not in KINDS:
        raise FeedbackError(f"未知反馈类型：{kind}")
    if not item_id:
        raise FeedbackError("item_id 不能为空")
    row = {
        "at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "id": item_id,
        "kind": kind,
        "note": note.strip(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, **row}


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def summarize(path: Path) -> dict:
    rows = load(path)
    by_kind = Counter(row["kind"] for row in rows)
    by_item = Counter(row["id"] for row in rows)
    return {
        "ok": True,
        "count": len(rows),
        "by_kind": dict(sorted(by_kind.items())),
        "by_item": [
            {"id": item_id, "count": count}
            for item_id, count in by_item.most_common()
        ],
    }


__all__ = ["FeedbackError", "KINDS", "add", "default_path", "load", "summarize"]
