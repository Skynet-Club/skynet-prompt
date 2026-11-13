#!/usr/bin/env python3
"""Claude Code UserPromptSubmit hook for the unified trigger."""

from __future__ import annotations

import json
import re
import sys

TRIGGER = re.compile(r"^\s*[；;]{2}([\s\S]*)$", re.UNICODE)


def context_for(prompt: str) -> str | None:
    if prompt.lstrip().startswith("；；；"):
        return None
    match = TRIGGER.match(prompt)
    if not match:
        return None
    query = match.group(1).strip()
    return "\n".join([
        "[skynet-prompt 已触发]",
        f"用户使用了统一触发器，查询内容：{query or '（空）'}",
        "请使用 skynet-prompt Skill 和已连接的 skynet-prompt MCP。",
        "先调用 prompt_search；如果查询是条目 id，调用 prompt_get。",
        "返回时展示 id、类目、作者、来源和可信状态；正文必须原样，不要改写。",
        "不要发送消息，不要修改仓库，不要读取凭据。",
    ])


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    prompt = payload.get("prompt") if isinstance(payload, dict) else None
    context = context_for(prompt) if isinstance(prompt, str) else None
    if context:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            },
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
