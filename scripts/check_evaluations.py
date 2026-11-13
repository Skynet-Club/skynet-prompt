#!/usr/bin/env python3
"""校验评测任务引用和格式。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.service import PromptService  # noqa: E402


def main() -> int:
    path = ROOT / "evaluations" / "tasks.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version 必须是 1")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 10:
        errors.append("至少需要 10 条评测任务")
        tasks = tasks or []
    ids = set()
    prompt_ids = {item["id"] for item in PromptService().items()}
    for task in tasks:
        task_id = task.get("id")
        if not task_id or task_id in ids:
            errors.append(f"任务 id 缺失或重复：{task_id}")
        ids.add(task_id)
        if task.get("prompt_id") not in prompt_ids:
            errors.append(f"{task_id}: prompt_id 不存在")
        criteria = task.get("criteria")
        if not task.get("task") or not isinstance(criteria, list) or not criteria:
            errors.append(f"{task_id}: 缺少 task/criteria")
    print(json.dumps({
        "ok": not errors,
        "count": len(tasks),
        "errors": errors,
    }, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
