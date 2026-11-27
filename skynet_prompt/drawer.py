"""``；；`` 提示词抽屉：左列场景、右列条目 + 预览。

不用 prompt_toolkit 的补全下拉（单列，放不下预览），而是挂进 Hermes TUI 自己的两个
扩展钩子：

- ``_get_extra_tui_widgets()``   → 抽屉这块 widget 出现在输入框上方
- ``_register_extra_tui_keybindings(kb, input_area)`` → ↑↓ / →← / Enter / Esc

宿主里只多一行 ``install(self)``；所有状态与绘制都在本文件。ASCII ``;;``
仅作为兼容别名。
"""

from __future__ import annotations

import textwrap
from typing import Iterable

from .menu import CATS, data_dir, load

DISPLAY = {key: name for name, key in CATS}

# 军旅绿：和 pi / opencode / DSH 选择器同一套色。
BG = "bg:#0c1109"
PANEL = "fg:#c9d5b7 bg:#131a0f"
MUTED = "fg:#839170 bg:#0c1109"
MUTED_PANEL = "fg:#839170 bg:#131a0f"
ACCENT = "fg:#a8c878 bg:#0c1109"
BORDER = "fg:#3b4a2e bg:#0c1109"
SELECTED = "fg:#f4f8e9 bg:#4e5f00"
SELECTED_DIM = "fg:#b9c7a5 bg:#303a00"

# 固定内容区高度；列表/正文长短都不改变抽屉高度。
BODY_ROWS = 14


def _cells(text: str) -> int:
    """终端里中文占两格，按显示宽度算而不是按字符数。"""
    from prompt_toolkit.utils import get_cwidth

    return get_cwidth(text)


def _clip(text: str, width: int) -> str:
    """截到 width 格，末尾补 `…`；不超宽就原样返回。"""
    text = " ".join(text.split())
    if width <= 1:
        return ""
    if _cells(text) <= width:
        return text
    out = ""
    for ch in text:
        if _cells(out + ch) > width - 1:
            break
        out += ch
    return out + "…"


def _pad(text: str, width: int) -> str:
    return text + " " * max(width - _cells(text), 0)


def _wrap(text: str, width: int, limit: int) -> list[str]:
    """按显示宽度折行（中文占两格），尽量在空格处断。"""
    text = " ".join(text.split())
    if not text:
        return [""]
    width = max(width, 8)
    lines: list[str] = []
    cur = ""
    for ch in text:
        if _cells(cur + ch) > width:
            cut = cur.rfind(" ")
            if cut > len(cur) // 2:
                lines.append(cur[:cut])
                cur = cur[cut + 1 :]
            elif ch in "。，、；：？！）】」』”’…":
                lines.append(cur[:-1])          # 标点不放到行首：提前一格断
                cur = cur[-1:]
            else:
                lines.append(cur)
                cur = ""
        cur += ch
    if cur:
        lines.append(cur)
    if len(lines) > limit:
        lines = lines[:limit]
        lines[-1] = _clip(lines[-1] + "…", width)
    return lines


def _at_second_semicolon(line_before_cursor: str) -> bool:
    """光标前最后一个字符是分号时，下一次分号键开抽屉。"""
    return bool(line_before_cursor) and line_before_cursor[-1] in (";", "；")


class Drawer:
    """两栏浏览器。状态只有「焦点在哪一栏 + 两栏各自的高亮行」。"""

    def __init__(self) -> None:
        self.items, _payload = load()
        self.counts = {key: 0 for _, key in CATS}
        for item in self.items:
            if item.get("cat") in self.counts:
                self.counts[item["cat"]] += 1
        self.cats = [(name, key) for name, key in CATS if self.counts.get(key)]
        self.open = False
        self.focus = "cats"          # cats / items / detail
        self.ci = 0
        self.ii = 0
        self.dscroll = 0             # 右侧正文滚动行
        self._detail_total = 0
        self.last = None             # 上一次补进去的 (起址, 文本)，供撤销
        self.buffer = None
        self.widget = None
        self.strip = None

    # -- 数据 -------------------------------------------------------------
    def rows(self) -> list[dict]:
        if not self.cats:
            return []
        key = self.cats[self.ci][1]
        return [i for i in self.items if i.get("cat") == key]

    def current(self) -> dict | None:
        rows = self.rows()
        if not rows:
            return None
        return rows[min(self.ii, len(rows) - 1)]

    # -- 键盘 -------------------------------------------------------------
    def key_down(self) -> None:
        if self.focus == "detail":
            self.dscroll = min(self.dscroll + 1, self._detail_scroll_max())
            return
        if self.focus == "cats":
            self.ci = min(self.ci + 1, len(self.cats) - 1)
            self.ii = 0
            self.dscroll = 0
        else:
            self.ii = min(self.ii + 1, max(len(self.rows()) - 1, 0))
            self.dscroll = 0

    def key_up(self) -> None:
        if self.focus == "detail":
            self.dscroll = max(self.dscroll - 1, 0)
            return
        if self.focus == "cats":
            self.ci = max(self.ci - 1, 0)
            self.ii = 0
            self.dscroll = 0
        else:
            self.ii = max(self.ii - 1, 0)
            self.dscroll = 0

    def key_right(self) -> None:
        if self.focus == "cats" and self.rows():
            self.focus = "items"
        elif self.focus == "items":
            self.focus = "detail"

    def key_left(self) -> None:
        self.focus = "items" if self.focus == "detail" else "cats"

    def _detail_scroll_max(self) -> int:
        return max(0, self._detail_total - BODY_ROWS)

    def close(self) -> None:
        self.open = False
        self.focus = "cats"

    def accept(self) -> None:
        item = self.current()
        if item is None:
            self.close()
            return
        if self.buffer is not None:
            start = self.buffer.cursor_position
            # 光标前是英文/符号时补一个空格，避免粘成 "do thisDo only…"
            before = self.buffer.text[:start]
            gap = " " if before and before[-1].isascii() and not before[-1].isspace() else ""
            self.buffer.insert_text(gap + item["zh"])
            self.last = {"start": start, "text": gap + item["zh"], "item": item}
        self.close()

    def undo(self) -> None:
        """把上一次补进去的那一段整段删掉。"""
        if not self.last or self.buffer is None:
            return
        start, text = self.last["start"], self.last["text"]
        self.buffer.cursor_position = min(start, len(self.buffer.text))
        self.buffer.delete(len(text))
        self.last = None

    # -- 绘制 -------------------------------------------------------------
    def _size(self) -> tuple[int, int]:
        try:
            from prompt_toolkit.application import get_app

            size = get_app().output.get_size()
            return size.columns, size.rows
        except Exception:
            return 100, 30

    @staticmethod
    def _widths(columns: int) -> tuple[int, int, int]:
        """1:1:2；两根竖线占 2 格，右栏最少 24 格。"""
        left_w = max(columns // 4, 18)
        mid_w = left_w
        right_w = max(columns - left_w - mid_w - 1, 24)
        return left_w, mid_w, right_w

    def _layout(self) -> tuple[list, list, list, int, int, int, int, int]:
        columns, _rows_avail = self._size()
        left_w, mid_w, right_w = self._widths(columns)
        all_rows = self.rows()
        left_rows = self.cats
        detail = self._detail_lines(self.current(), right_w)
        self._detail_total = len(detail)
        body = BODY_ROWS
        start = 0
        if len(all_rows) > body:
            start = max(0, min(self.ii - body + 1, len(all_rows) - body))
        rows = all_rows[start:start + body]
        return left_rows, rows, detail, body, start, left_w, mid_w, right_w

    def fragments(self) -> list[tuple[str, str]]:
        columns, _rows_avail = self._size()
        left_rows, rows, detail, body, start, left_w, mid_w, right_w = self._layout()
        all_rows = self.rows()
        dstart = min(self.dscroll, self._detail_scroll_max())
        self.dscroll = dstart
        out: list[tuple[str, str]] = []

        def line(*parts: tuple[str, str]) -> None:
            for style, text in parts:
                out.append((style, text))
            out.append(("", "\n"))

        head = f" 提示词补充 · {len(self.items)} 条 / {len(self.cats)} 场景"
        if self.focus == "detail":
            hint = "↑↓ 滚动正文 · ← 回条目 · Enter 补入 · Esc 关闭"
        elif self.focus == "items":
            hint = "↑↓ 选条目 · ← 场景 · → 正文 · Enter 补入 · Esc 关闭"
        else:
            hint = "↑↓ 选场景 · → 看条目 · Enter 补入 · Esc 关闭"
        if self.last:
            head += "   · 已补 1 层"
        room = columns - _cells(head) - 3
        shown_hint = hint if _cells(hint) <= room else _clip(hint, max(room, 0))
        line((ACCENT, head), (MUTED, "   " + shown_hint))
        line((BORDER, "─" * columns))

        for i in range(body):
            # 左栏：场景
            if i < len(left_rows):
                cname, ckey = left_rows[i]
                active = i == self.ci
                focus = active and self.focus == "cats"
                mark = "▸ " if active else "  "
                label = _pad(_clip(mark + cname, left_w - 6), left_w - 6)
                out.append((SELECTED if focus else SELECTED_DIM if active else PANEL,
                            f"{label}{self.counts[ckey]:>4} "))
            else:
                out.append((PANEL, " " * (left_w - 1)))
            out.append((BORDER, "│"))

            # 中栏：条目
            if i < len(rows):
                row = rows[i]
                at = start + i
                active = at == self.ii
                focus = active and self.focus == "items"
                mark = "▸ " if active else "  "
                label = _pad(_clip(mark + row.get("zh", ""), mid_w), mid_w)
                out.append((SELECTED if focus else SELECTED_DIM if active else PANEL, label))
            else:
                out.append((PANEL, " " * mid_w))
            out.append((BORDER, "│"))

            # 右栏：完整正文；进入正文栏后可 ↑↓ 滚动。
            if dstart + i < len(detail):
                style, text = detail[dstart + i]
                out.append((style, _pad(_clip(text, right_w), right_w)))
            else:
                out.append((PANEL, " " * right_w))
            out.append(("", "\n"))

        more = len(all_rows) - start - len(rows)
        note = f"共 {len(all_rows)} 条" + (f" · 下面还有 {more} 条" if more else "")
        if detail:
            note += f" · 正文 {dstart + 1}-{min(dstart + body, len(detail))}/{len(detail)}"
        line((MUTED, _clip(note, columns)))
        return out

    def _detail_lines(self, item, width: int) -> list[tuple[str, str]]:
        """右栏：中文正文全量优先，其次出处；不折行到左中栏。"""
        if item is None:
            return [(MUTED_PANEL, _clip("（该场景没有条目）", width))]
        out: list[tuple[str, str]] = []
        text_w = max(width - 6, 10)
        for n, seg in enumerate(_wrap(item.get("zh", ""), text_w, 2000)):
            prefix = "中文  " if n == 0 else " " * 6
            out.append((PANEL, _clip(prefix + seg, width)))
        out.append((PANEL, ""))
        meta = f"作者  {item.get('author', '')} · {item.get('date', '')}"
        out.append((MUTED_PANEL, _clip(meta, width)))
        out.append((MUTED_PANEL, _clip(f"链接  {item.get('url', '')}", width)))
        if item.get("en"):
            out.append((PANEL, ""))
            label = "原文（节选）" if item.get("excerpt") else "原文"
            out.append((MUTED_PANEL, label))
            for seg in _wrap(item.get("en", ""), text_w, 2000):
                out.append((MUTED_PANEL, _clip(" " * 6 + seg, width)))
        return out

    def height(self) -> int:
        if not self.open:
            return 0
        return 2 + BODY_ROWS + 1

    # -- 安装 -------------------------------------------------------------
    def install(self, cli) -> None:
        from prompt_toolkit.filters import Condition
        from prompt_toolkit.keys import Keys
        from prompt_toolkit.layout import ConditionalContainer, Window
        from prompt_toolkit.layout.controls import FormattedTextControl

        self.widget = ConditionalContainer(
            Window(FormattedTextControl(self.fragments), wrap_lines=False,
                   height=self.height, style=BG),
            filter=Condition(lambda: self.open),
        )
        self.strip = ConditionalContainer(
            Window(FormattedTextControl(self.strip_fragments), height=1,
                   wrap_lines=False, style=BG),
            filter=Condition(lambda: self.last is not None),
        )

        prev_extra = cli._get_extra_tui_widgets
        cli._get_extra_tui_widgets = lambda: [*prev_extra(), self.widget, self.strip]

        prev_kb = cli._register_extra_tui_keybindings

        def extra_kb(kb, *, input_area):
            prev_kb(kb, input_area=input_area)
            self.buffer = input_area.buffer
            self._bind(kb, Condition)

        cli._register_extra_tui_keybindings = extra_kb
        cli._skynet_prompt_drawer = self

    def strip_fragments(self) -> list[tuple[str, str]]:
        """输入框上方那一行「已补 …」，让人知道刚才补了什么、怎么撤。"""
        if not self.last:
            return []
        item = self.last.get("item") or {}
        name = next((n for n, k in CATS if k == item.get("cat")), "")
        title = _clip(item.get("zh", ""), 28)
        return [(MUTED, f" 已补 1 层 · {name} · {title} "),
                (MUTED, "  "),
                (ACCENT, "⌥Z 撤销")]

    def _bind(self, kb, Condition) -> None:
        from prompt_toolkit.application import get_app
        from prompt_toolkit.keys import Keys

        is_open = Condition(lambda: self.open)

        def repaint() -> None:
            get_app().invalidate()

        def at_second_semicolon() -> bool:
            """光标前是分号时，再按一次就开抽屉；前面的文字保留。

            不再要求行首或空输入框：
            - ``你好；；``、``;;`` 都能开
            - 句子里已有的分号（后面不是分号）不开
            """
            if self.open or self.buffer is None:
                return False
            return _at_second_semicolon(self.buffer.document.current_line_before_cursor)

        def open_drawer(event) -> None:
            if self.buffer is not None:
                # 吃掉已经落在输入框里的那个分号
                self.buffer.delete_before_cursor(1)
                self.buffer.cancel_completion()
            self.open = True
            self.focus = "cats"
            self.ci = min(self.ci, max(len(self.cats) - 1, 0))
            self.ii = 0
            self.dscroll = 0
            repaint()

        kb.add(";", filter=Condition(at_second_semicolon), eager=True)(open_drawer)
        kb.add("；", filter=Condition(at_second_semicolon), eager=True)(open_drawer)

        def _ignore(event) -> None:
            return None

        # 抽屉打开时不再搜索，也不要把字打进后面的输入框。
        kb.add(Keys.Any, filter=is_open)(_ignore)
        kb.add("backspace", filter=is_open)(_ignore)

        kb.add("up", filter=is_open, eager=True)(lambda e: (self.key_up(), repaint()))
        kb.add("down", filter=is_open, eager=True)(lambda e: (self.key_down(), repaint()))
        kb.add("right", filter=is_open, eager=True)(lambda e: (self.key_right(), repaint()))
        kb.add("left", filter=is_open, eager=True)(lambda e: (self.key_left(), repaint()))
        kb.add("enter", filter=is_open, eager=True)(lambda e: (self.accept(), repaint()))
        kb.add("escape", filter=is_open, eager=True)(lambda e: (self.close(), repaint()))
        kb.add("c-c", filter=is_open, eager=True)(lambda e: (self.close(), repaint()))


        def _undo(event) -> None:
            self.undo()
            repaint()

        kb.add("escape", "z", eager=True)(_undo)    # ⌥Z 撤销上一次补的那一段


def install(cli) -> None:
    """宿主入口：装一次，失败就当没装。"""
    Drawer().install(cli)
