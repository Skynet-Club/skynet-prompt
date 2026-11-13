"""来源与翻译审核账本。

审核决定绑定到条目内容摘要；正文或来源变化后，旧审核自动失效。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .safety import scan_item


class ReviewError(ValueError):
    pass


def item_sha256(item: dict) -> str:
    source = item.get("source") or {}
    body = {
        "id": item["id"],
        "en": item["en"],
        "zh": item["zh"],
        "url": item["url"],
        "source_quote": source.get("quote", ""),
        "source_url": source.get("url", ""),
        "verdict": (item.get("evidence") or {}).get("verdict", ""),
    }
    encoded = json.dumps(
        body,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_ledger(decisions: dict, items: list[dict]) -> dict:
    if not isinstance(decisions, dict) or decisions.get("schema_version") != 1:
        raise ReviewError("审核决定 schema_version 必须是 1")
    reviewer = decisions.get("reviewer")
    if not isinstance(reviewer, dict) or not reviewer.get("id") or not reviewer.get("kind"):
        raise ReviewError("审核决定缺少 reviewer.id/kind")
    method = decisions.get("method")
    safety_method = decisions.get("safety_method")
    reviewed_at = decisions.get("reviewed_at")
    if not method or not safety_method or not reviewed_at:
        raise ReviewError("审核决定缺少 method/safety_method/reviewed_at")

    approved = decisions.get("approved_items")
    if not isinstance(approved, list) or not all(isinstance(value, str) for value in approved):
        raise ReviewError("approved_items 必须是字符串数组")
    if len(set(approved)) != len(approved):
        raise ReviewError("approved_items 有重复 id")

    by_id = {item["id"]: item for item in items}
    missing = [item_id for item_id in approved if item_id not in by_id]
    if missing:
        raise ReviewError("审核决定引用不存在条目：" + ", ".join(missing))
    unverified = [
        item_id for item_id in approved
        if (by_id[item_id].get("evidence") or {}).get("verdict") == "unverified"
    ]
    if unverified:
        raise ReviewError("未核实条目不能通过正式审核：" + ", ".join(unverified))

    rows = {}
    for item_id in approved:
        item = by_id[item_id]
        safety = scan_item(item)
        if safety["status"] != "passed":
            raise ReviewError(f"安全扫描未通过，不能批准：{item_id}")
        rows[item_id] = {
            "source": "reviewed",
            "translation": "reviewed",
            "safety": "reviewed",
            "reviewer": reviewer,
            "method": method,
            "safety_method": safety_method,
            "reviewed_at": reviewed_at,
            "item_sha256": item_sha256(item),
        }
    return {
        "schema_version": 1,
        "generated_at": reviewed_at,
        "items": rows,
    }


def validate_ledger(ledger: dict, items: list[dict]) -> None:
    if not isinstance(ledger, dict) or ledger.get("schema_version") != 1:
        raise ReviewError("审核账本 schema_version 必须是 1")
    rows = ledger.get("items")
    if not isinstance(rows, dict):
        raise ReviewError("审核账本缺少 items 对象")
    by_id = {item["id"]: item for item in items}
    for item_id, review in rows.items():
        if item_id not in by_id:
            raise ReviewError(f"审核账本引用不存在条目：{item_id}")
        if not isinstance(review, dict):
            raise ReviewError(f"审核账本条目格式错误：{item_id}")
        if review.get("item_sha256") != item_sha256(by_id[item_id]):
            raise ReviewError(f"条目变更后旧审核已失效：{item_id}")
        if (
            review.get("source") != "reviewed"
            or review.get("translation") != "reviewed"
            or review.get("safety") != "reviewed"
        ):
            raise ReviewError(f"审核账本未完成来源、翻译与安全审核：{item_id}")


def load_ledger(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewError(f"审核账本不可读：{path}（{exc}）") from exc


__all__ = [
    "ReviewError",
    "build_ledger",
    "item_sha256",
    "load_ledger",
    "validate_ledger",
]
