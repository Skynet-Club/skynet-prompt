"""``；；`` 提示词补充：prompt_toolkit 补全器。

一级：``；；`` → 九个类目（右侧显示条数）
二级：``；；定验收`` → 该类条目（正文=中文直译，右侧=作者）
选中：把触发器与查询整段替换成该条目，光标停在末尾，不发送。
ASCII ``;;`` 仅作为兼容别名。
"""

from __future__ import annotations

import re
from typing import Iterator

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from .catalog import CATS, DISPLAY, data_dir, default_catalog


def load() -> tuple[list[dict], dict]:
    """读快照。缺失或损坏时抛 RuntimeError，调用方负责打印到 stderr。"""
    catalog = default_catalog().load()
    return catalog.items(), {"packs": catalog.packs()}


def in_code_block(text_before_cursor: str) -> bool:
    """``` 开合未配对即视为在代码块内。"""
    fences = sum(1 for line in text_before_cursor.splitlines() if line.startswith("```"))
    return fences % 2 == 1


def _clip(text: str, width: int = 40) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


class PromptMenuCompleter(Completer):
    """``;;`` 开头（且只在行首）时接管补全，其余情况一律不介入。"""

    def __init__(self) -> None:
        self._items: list[dict] | None = None
        self._meta: dict = {}
        self._error: str | None = None

    # -- 数据 ---------------------------------------------------------------
    def _catalog(self) -> list[dict]:
        if self._items is None and self._error is None:
            try:
                self._items, self._meta = load()
            except RuntimeError as exc:
                self._error = str(exc)
                import sys

                print(f"[skynet-prompt] {exc}", file=sys.stderr)
        return self._items or []

    def counts(self) -> dict[str, int]:
        counts = {key: 0 for _, key in CATS}
        for item in self._catalog():
            if item.get("cat") in counts:
                counts[item["cat"]] += 1
        return counts

    # -- 补全 ---------------------------------------------------------------
    def get_completions(self, document: Document, complete_event) -> Iterator[Completion]:
        line = document.current_line_before_cursor
        # 光标前最近的 ;; 或 ；；；前面的文字原样保留
        matches = list(re.finditer(r"[;；]{2}", line))
        if not matches:
            return
        if in_code_block(document.text_before_cursor):
            return
        last = matches[-1]
        trigger = last.group(0)
        token = line[last.end():]
        if " " in token:
            return
        yield from self._complete(token, trigger + token, trigger)

    def _complete(self, token: str, word: str, trigger: str) -> Iterator[Completion]:
        items = self._catalog()
        if not items:
            return
        counts = self.counts()

        hit = next(((name, key) for name, key in CATS if name == token), None)
        if hit is not None:
            name, key = hit
            rows = [i for i in items if i.get("cat") == key]
            for item in rows:
                yield Completion(
                    item["zh"],
                    start_position=-len(word),
                    display=_clip(item["zh"]),
                    display_meta=item.get("author", ""),
                )
            return

        for name, key in CATS:
            if counts[key] == 0:
                continue
            if not name.startswith(token):
                continue
            yield Completion(
                trigger + name,
                start_position=-len(word),
                display=name,
                display_meta=f"{counts[key]} 条",
            )


def get_completer() -> PromptMenuCompleter | None:
    """给宿主用：数据不可用时返回 None，宿主保持原样（不接管补全）。"""
    completer = PromptMenuCompleter()
    if not completer._catalog():
        return None
    return completer
