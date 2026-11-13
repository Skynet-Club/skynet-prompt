#!/usr/bin/env python3
"""面向用户的一步安装入口；内部复用可验证的 agent_install。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT_INSTALL = ROOT / "scripts" / "agent_install.py"


def run_agent(mode: str, adapters: list[str]) -> tuple[int, dict]:
    command = [sys.executable, str(AGENT_INSTALL), f"--{mode}"]
    for adapter in adapters:
        command.extend(["--adapter", adapter])
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError:
        report = {
            "ok": False,
            "status": "bootstrap-error",
            "error": completed.stderr.strip() or completed.stdout.strip(),
        }
    return completed.returncode, report


def show_plan(plan: dict) -> None:
    print(f"skynet-prompt {plan.get('version', '')} 安装计划")
    print(f"统一触发器：{plan.get('trigger', '；；')}")
    print("\n检测到的 Agent：")
    for row in plan.get("detected", []):
        if not row.get("available"):
            continue
        version = row.get("version") or "版本未知"
        state = "可用" if row.get("compatible") else f"跳过：{row.get('reason')}"
        print(f"  {row['id']:10} {version:18} {state}")
    print("\n将安装：")
    for adapter in plan.get("selected", []):
        print(f"  ✓ {adapter}")
    print("\n将修改：")
    for change in plan.get("changes", []):
        print(f"  · {change}")
    print("\n安装后验证：psup selftest + psup doctor")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="一条命令检测并安装 skynet-prompt")
    parser.add_argument("--adapter", action="append", default=[])
    parser.add_argument("--apply", action="store_true", help="确认计划后直接安装")
    parser.add_argument("--yes", action="store_true", help="--apply 的同义参数")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args(argv)

    code, plan = run_agent("plan", args.adapter)
    if code != 0 or not plan.get("ok"):
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return code or 1
    if not args.json:
        show_plan(plan)

    should_apply = args.apply or args.yes
    if not should_apply and sys.stdin.isatty():
        answer = input("\n现在安装？[y/N] ").strip().lower()
        should_apply = answer in {"y", "yes"}
    if not should_apply:
        if args.json:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print("\n只完成了检测。运行 ./skynet-prompt-bootstrap --apply 执行安装。")
        return 0

    selected = plan.get("selected", [])
    code, result = run_agent("apply", selected)
    if not args.json:
        print("\n安装完成。" if code == 0 else "\n安装失败。")
        verification = result.get("verification") or {}
        if verification:
            print(f"验证：{'PASS' if verification.get('ok') else 'FAIL'}")
        print(f"入口：{result.get('trigger', '；；')}")
        if result.get("rollback"):
            print(f"卸载：{result['rollback'][0]}")
    else:
        result["plan"] = plan
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
