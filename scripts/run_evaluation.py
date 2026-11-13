#!/usr/bin/env python3
"""运行基线 vs 提示词增强的盲评对照。

使用 OpenAI-compatible chat completions。API key 只从环境变量读取，不落盘、不打印。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.service import PromptService  # noqa: E402
from skynet_prompt.advisor import suggest  # noqa: E402


def chat(base: str, key: str, model: str, prompt: str, *, max_tokens: int = 600) -> str:
    body = json.dumps({
        "model": model,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"].strip()


def judge(
    base: str,
    key: str,
    model: str,
    task: dict,
    first: str,
    second: str,
    *,
    first_label: str,
) -> dict:
    prompt = f"""你是独立的任务质量评审。根据任务和 criteria 比较回答 A 与回答 B。
不要因为长度、格式或自信语气加分；只判断是否满足 criteria。

任务：{task['task']}
criteria：{"；".join(task['criteria'])}

回答 A：
{first}

回答 B：
{second}

只输出 JSON：{{"winner":"A|B|tie","reason":"不超过40字"}}。
"""
    raw = chat(base, key, model, prompt, max_tokens=1200)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        return {"winner": "tie", "reason": "judge_non_json", "raw": raw[:200]}
    try:
        result = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return {"winner": "tie", "reason": "judge_bad_json", "raw": raw[:200]}
    winner = result.get("winner")
    if winner not in {"A", "B", "tie"}:
        winner = "tie"
    mapped = (
        first_label if winner == "A"
        else ("augmented" if first_label == "baseline" else "baseline")
        if winner == "B"
        else "tie"
    )
    return {"winner": mapped, "reason": str(result.get("reason", ""))[:200]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "evaluations" / "results.json")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--judge-model", default="")
    parser.add_argument("--base", default="https://api.deepseek.com")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--selection", choices=["fixed", "advisor"], default="fixed")
    parser.add_argument(
        "--from-results",
        type=Path,
        help="复用已有 baseline/augmented 输出，只重新盲评",
    )
    args = parser.parse_args()

    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        print(json.dumps({
            "ok": False,
            "error": "DEEPSEEK_API_KEY is required",
        }, ensure_ascii=False))
        return 2

    base_tasks = json.loads(
        (ROOT / "evaluations" / "tasks.json").read_text(encoding="utf-8")
    )["tasks"][: args.limit]
    tasks = [
        {**task, "id": f"{task['id']}-r{repeat + 1}"}
        for repeat in range(max(args.repeats, 1))
        for task in base_tasks
    ]
    service = PromptService()
    rows = []
    if args.from_results:
        previous = json.loads(args.from_results.read_text(encoding="utf-8"))
        source_rows = previous["rows"][: args.limit]
    else:
        source_rows = tasks
    for index, task in enumerate(source_rows):
        items = service.items()
        if args.from_results:
            baseline = task["baseline"]
            augmented = task["augmented"]
            selected_prompt_id = task.get("selected_prompt_id", task.get("prompt_id"))
        elif args.selection == "advisor":
            candidates = suggest(items, task["task"], limit=1)
            if candidates:
                item = service.get(candidates[0]["id"])
            else:
                item = service.get(task["prompt_id"])
            selected_prompt_id = item["id"]
        else:
            item = service.get(task["prompt_id"])
            selected_prompt_id = item["id"]
        if not args.from_results:
            baseline_prompt = f"请完成任务：\n{task['task']}"
            augmented_prompt = (
                f"请完成任务：\n{task['task']}\n\n"
                f"把下面的提示词作为附加约束执行，不要复述它：\n{item['zh']}"
            )
            baseline = chat(args.base, key, args.model, baseline_prompt)
            augmented = chat(args.base, key, args.model, augmented_prompt)
        judge_model = args.judge_model or args.model
        if index % 2 == 0:
            verdict = judge(
                args.base, key, judge_model, task,
                baseline, augmented, first_label="baseline",
            )
        else:
            verdict = judge(
                args.base, key, judge_model, task,
                augmented, baseline, first_label="augmented",
            )
        rows.append({
            "id": task["id"],
            "prompt_id": task["prompt_id"],
            "selected_prompt_id": selected_prompt_id,
            "task": task["task"],
            "criteria": task["criteria"],
            "baseline": baseline,
            "augmented": augmented,
            "verdict": verdict,
        })
        print(f"{task['id']}: {verdict['winner']} {verdict['reason']}", file=sys.stderr, flush=True)

    winners = {"baseline": 0, "augmented": 0, "tie": 0}
    for row in rows:
        winners[row["verdict"]["winner"]] += 1
    result = {
        "ok": True,
        "model": args.model,
        "judge_model": args.judge_model or args.model,
        "method": "blind-pairwise-single-model",
        "selection": args.selection,
        "checked_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "count": len(rows),
        "repeats": max(args.repeats, 1),
        "wins": winners,
        "augmented_win_rate": round(
            winners["augmented"] / max(len(rows), 1),
            3,
        ),
        "rows": rows,
    }
    args.out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "count": len(rows),
        "wins": winners,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
