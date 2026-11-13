"""``；；`` 提示词抽屉：左列类目、右列条目 + 预览。

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

SELECTED = "reverse"
DIM = "fg:ansibrightblack"


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
        self.focus = "cats"          # cats / items
        self.ci = 0
        self.ii = 0
        self.query = ""              # 抽屉里打的字 → 全库过滤
        self.last = None             # 上一次补进去的 (起址, 文本)，供撤销
        self.buffer = None
        self.widget = None
        self.strip = None

    # -- 数据 -------------------------------------------------------------
    @staticmethod
    def _haystack(item: dict) -> str:
        """搜得到的字段：中文、原文、作者、类目名——用户想按类目名找也能命中所属条目。"""
        return " ".join((
            item.get("zh", ""), item.get("en", ""),
            item.get("author", ""), DISPLAY.get(item.get("cat"), ""),
        )).casefold()

    def rows(self) -> list[dict]:
        if self.query:
            q = self.query.casefold()
            return [i for i in self.items if q in self._haystack(i)]
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
        if self.focus == "cats" and not self.query:
            self.ci = min(self.ci + 1, len(self.cats) - 1)
            self.ii = 0
        else:
            self.ii = min(self.ii + 1, max(len(self.rows()) - 1, 0))

    def key_up(self) -> None:
        if self.focus == "cats" and not self.query:
            self.ci = max(self.ci - 1, 0)
            self.ii = 0
        else:
            self.ii = max(self.ii - 1, 0)

    def key_right(self) -> None:
        if self.rows():
            self.focus = "items"

    def key_left(self) -> None:
        self.focus = "cats"

    def type_char(self, text: str) -> None:
        self.query += text
        self.focus = "items"
        self.ii = 0

    def backspace(self) -> None:
        self.query = self.query[:-1]
        self.ii = 0
        if not self.query:
            self.focus = "cats"

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

    def fragments(self) -> list[tuple[str, str]]:
        columns, _rows_avail = self._size()
        left_w = 22
        right_w = max(columns - left_w - 4, 30)
        out: list[tuple[str, str]] = []

        def line(*parts: tuple[str, str]) -> None:
            for style, text in parts:
                out.append((style, text))
            out.append(("", "\n"))

        rows = self.rows()
        if self.query:
            head = f" 提示词补充 · 搜索「{self.query}」· {len(rows)} 条"
            hint = "↑↓ 选 · Enter 补进输入框 · ⌫ 删字 · Esc 关闭"
        else:
            head = f" 提示词补充 · {len(self.items)} 条 / {len(self.cats)} 类"
            hint = "↑↓ 选类目 · → 看条目 · Enter 补进输入框 · 直接打字可搜全库 · Esc 关闭"
        if self.last:
            head += "   · 已补 1 层"
        room = columns - _cells(head) - 3
        line((DIM, head), (DIM, "   " + (hint if _cells(hint) <= room else _clip(hint, max(room, 0)))))
        line((DIM, "─" * columns))

        item = self.current()
        left_rows = [] if self.query else self.cats
        # 条目多于一屏时只画一窗，窗口跟着选中项走（全库搜索能命中几十条）
        all_rows = rows
        max_body = 10
        start = 0
        if len(all_rows) > max_body and self.focus == "items":
            start = max(0, min(self.ii - max_body + 1, len(all_rows) - max_body))
        rows = all_rows[start : start + max_body]
        sel = (min(self.ii, len(all_rows) - 1) - start) if all_rows else -1
        if len(left_rows) > max_body:
            left_rows = left_rows[:max_body]
        body = max(len(left_rows), len(rows), 1)

        def item_line(at: int, r: dict) -> None:
            selected = self.focus == "items" and at == sel
            author = r.get("author", "")
            label = _clip(("▸ " if at == sel else "  ") + r["zh"],
                          right_w - _cells(author) - 3)
            out.append((SELECTED if selected else "",
                        " " + _pad(label, right_w - _cells(author) - 2) + author))

        for i in range(body):
            # 左栏：类目（定宽，右侧条数不挪位）；搜索时左栏只留一行说明
            if self.query:
                if i == 0:
                    label = _pad(_clip("▸ 搜索", left_w - 6), left_w - 6)
                    out.append((SELECTED, f"{label}{len(all_rows):>4} │"))
                else:
                    out.append(("", " " * left_w + "│"))
            elif i < len(left_rows):
                cname, ckey = self.cats[i]
                selected = self.focus == "cats" and i == self.ci
                current = i == self.ci
                mark = "▸ " if current else "  "
                label = _pad(_clip(mark + cname, left_w - 6), left_w - 6)
                left = f"{label}{self.counts[ckey]:>4} │"
                out.append((SELECTED if selected else "", left))  # selected = 焦点在本栏
            else:
                out.append(("", " " * left_w + "│"))
            # 右栏：条目（中文截断，作者右对齐）
            if i < len(rows):
                item_line(i, rows[i])
            out.append(("", "\n"))

        if start or (len(all_rows) > max_body):
            more = len(all_rows) - start - len(rows)
            tail = " " * (left_w + 1) + "│ "
            note = f"共 {len(all_rows)} 条，下面还有 {more} 条" if more else f"共 {len(all_rows)} 条"
            line((DIM, tail + note))

        # 预览：选中条目全文
        out.extend(self._preview_lines(item, left_w, right_w))
        return out

    def _preview_lines(self, item, left_w: int, right_w: int) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []

        def line(*parts: tuple[str, str]) -> None:
            for style, text in parts:
                out.append((style, text))
            out.append(("", "\n"))

        line((DIM, " " * (left_w + 1) + "└" + "─" * max(right_w, 10)))
        if item is None:
            msg = "没有匹配，⌫ 改字或 Esc 退出" if self.query else "（该类没有条目）"
            line((DIM, " " * (left_w + 2) + msg))
            return out
        pad = " " * (left_w + 2)
        label_w = 4
        en_label = "原文（节选）" if item.get("excerpt") else "原文"
        for label, value in ((en_label, item.get("en", "")), ("中文", item.get("zh", ""))):
            for n, seg in enumerate(_wrap(value, right_w - label_w - 2, 2)):
                line((DIM, pad + (label if n == 0 else " " * label_w) + "  "), ("", seg))
        meta = f"{item.get('author', '')} · {item.get('date', '')}"
        line((DIM, pad + "作者  "), ("", _clip(meta, right_w - 8)))
        line((DIM, pad + "性质  "), ("", _clip(item.get("nature", "未核实"), right_w - 8)))
        line((DIM, pad + "链接  "), ("", _clip(item.get("url", ""), right_w - 8)))
        return out

    def height(self) -> int:
        if not self.open:
            return 0
        columns, _ = self._size()
        left_w, right_w = 22, max(columns - 26, 30)
        total = len(self.rows())
        body = max(1 if self.query else min(len(self.cats), 10), min(total, 10), 1)
        preview = len(self._preview_lines(self.current(), left_w, right_w)) // 2
        return 2 + body + (1 if total > 10 else 0) + preview

    # -- 安装 -------------------------------------------------------------
    def install(self, cli) -> None:
        from prompt_toolkit.filters import Condition
        from prompt_toolkit.keys import Keys
        from prompt_toolkit.layout import ConditionalContainer, Window
        from prompt_toolkit.layout.controls import FormattedTextControl

        self.widget = ConditionalContainer(
            Window(FormattedTextControl(self.fragments), wrap_lines=False,
                   height=self.height),
            filter=Condition(lambda: self.open),
        )
        self.strip = ConditionalContainer(
            Window(FormattedTextControl(self.strip_fragments), height=1, wrap_lines=False),
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
        return [(DIM, f" 已补 1 层 · {name} · {title} "),
                ("", "  "),
                (DIM, "⌥Z 撤销")]

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
            self.query = ""
            self.focus = "cats"
            self.ci = min(self.ci, max(len(self.cats) - 1, 0))
            self.ii = 0
            repaint()

        kb.add(";", filter=Condition(at_second_semicolon), eager=True)(open_drawer)
        kb.add("；", filter=Condition(at_second_semicolon), eager=True)(open_drawer)

        kb.add("up", filter=is_open, eager=True)(lambda e: (self.key_up(), repaint()))
        kb.add("down", filter=is_open, eager=True)(lambda e: (self.key_down(), repaint()))
        kb.add("right", filter=is_open, eager=True)(lambda e: (self.key_right(), repaint()))
        kb.add("left", filter=is_open, eager=True)(lambda e: (self.key_left(), repaint()))
        kb.add("enter", filter=is_open, eager=True)(lambda e: (self.accept(), repaint()))
        kb.add("escape", filter=is_open, eager=True)(lambda e: (self.close(), repaint()))
        kb.add("c-c", filter=is_open, eager=True)(lambda e: (self.close(), repaint()))
        kb.add("backspace", filter=is_open, eager=True)(lambda e: (self.backspace(), repaint()))

        def _type(event) -> None:
            if event.data and event.data.isprintable():
                self.type_char(event.data)
                repaint()

        kb.add(Keys.Any, filter=is_open)(_type)     # 抽屉里直接打字 = 全库搜

        def _undo(event) -> None:
            self.undo()
            repaint()

        kb.add("escape", "z", eager=True)(_undo)    # ⌥Z 撤销上一次补的那一段


def install(cli) -> None:
    """宿主入口：装一次，失败就当没装。"""
    Drawer().install(cli)
