"""统一的用户触发协议。"""

from __future__ import annotations

CANONICAL_TRIGGER = "；；"
ASCII_TRIGGER = ";;"
TRIGGER_ALIASES = (CANONICAL_TRIGGER, ASCII_TRIGGER)
LITERAL_ESCAPE = "；；；"


def strip_leading_trigger(text: str) -> str | None:
    """去掉消息开头的主触发器或兼容触发器，返回后续查询。"""
    if text.startswith(LITERAL_ESCAPE):
        return None
    for trigger in TRIGGER_ALIASES:
        if text.startswith(trigger):
            return text[len(trigger):].lstrip()
    return None
