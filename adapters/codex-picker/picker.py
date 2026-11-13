#!/usr/bin/env python3
"""Codex 外部编辑器里的提示词抽屉。

Codex 的 Ctrl+G 会把当前草稿写进一个临时文件，调用 $VISUAL/$EDITOR，
再把编辑后的文件内容放回输入框。本脚本就是这个“编辑器”：

- 草稿里没有 `;;`：交给 psup-editor.sh 回退到普通编辑器
- 草稿里有 `;;`：打开两级抽屉，选中后把 `;;` 替换成 zh 原文

键位：↑↓ 选择 · → 进列表 · ← 回类目 · Enter 插入 · Esc 取消
"""

from __future__ import annotations

import argparse
import curses
import json
import locale
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"

ORIGIN = {
    "verbatim": "本人原话",
    "compilation": "他人整理",
    "unverified": "未核实",
}


def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def text_width(text: str) -> int:
    return sum(char_width(ch) for ch in text)


def fit(text: str, limit: int) -> str:
    """按显示宽度截断，保留一个省略号。"""
    if limit <= 0:
        return ""
    out: list[str] = []
    used = 0
    for ch in text:
        cw = char_width(ch)
        if used + cw > limit - 1:
            out.append("…")
            break
        out.append(ch)
        used += cw
    return "".join(out)


def wrap(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    current = ""
    used = 0
    for ch in " ".join(text.split()):
        cw = char_width(ch)
        if used + cw > limit:
            lines.append(current)
            current = ""
            used = 0
        current += ch
        used += cw
    if current:
        lines.append(current)
    return lines or [""]


def find_trigger(text: str) -> int:
    """最后一个 ;; 或 ；；。"""
    matches = list(re.finditer(r"[;；]{2}", text))
    return matches[-1].start() if matches else -1


def apply_selection(seed: str, zh: str) -> str:
    index = find_trigger(seed)
    if index < 0:
        return seed
    return seed[:index] + zh + seed[index + 2 :]


def load_cats() -> list[dict]:
    index = json.loads((CONTENT / "index.json").read_text(encoding="utf-8"))
    names = index.get("cat_names", {})
    items = []
    for row in index["items"]:
        base = CONTENT / "items" / row["id"]
        items.append({
            **row,
            "zh": (base / "zh.txt").read_text(encoding="utf-8"),
            "en": (base / "en.txt").read_text(encoding="utf-8"),
        })
    return [
        {
            "key": key,
            "name": names.get(key, key),
            "items": [item for item in items if item["cat"] == key],
        }
        for key in index["cats"]
    ]


class Picker:
    def __init__(self, screen, cats: list[dict]) -> None:
        self.screen = screen
        self.cats = cats
        self.col = 0
        self.cat_index = 0
        self.item_index = 0
        self.pairs = {}

    @property
    def cat(self) -> dict:
        return self.cats[self.cat_index]

    @property
    def item(self) -> dict:
        return self.cat["items"][self.item_index]

    def init_colors(self) -> None:
        try:
            curses.start_color()
            curses.use_default_colors()
            self.pairs = {
                "accent": curses.color_pair(1),
                "dim": curses.color_pair(2),
                "meta": curses.color_pair(3),
            }
        except curses.error:
            self.pairs = {"accent": 0, "dim": 0, "meta": 0}

    def put(self, y: int, x: int, text: str, attr: int = 0) -> None:
        height, width = self.screen.getmaxyx()
        if y < 0 or y >= height or x >= width:
            return
        try:
            self.screen.addstr(y, x, fit(text, width - x - 1), attr)
        except curses.error:
            pass

    def move(self, delta: int) -> None:
        if self.col == 0:
            self.cat_index = (self.cat_index + delta + len(self.cats)) % len(self.cats)
            self.item_index = 0
        else:
            count = len(self.cat["items"])
            self.item_index = (self.item_index + delta + count) % count

    def draw(self) -> None:
        screen = self.screen
        screen.erase()
        height, width = screen.getmaxyx()
        if height < 12 or width < 40:
            self.put(0, 0, "终端太小，至少需要 40x12")
            screen.refresh()
            return

        accent = self.pairs["accent"] | curses.A_BOLD
        dim = self.pairs["dim"] | curses.A_DIM
        meta = self.pairs["meta"]

        total = sum(len(cat["items"]) for cat in self.cats)
        self.put(0, 0, f"提示词补充 · {total} 条 / {len(self.cats)} 类 · 中文直译", accent)
        self.put(1, 0, "↑↓ 选择 · → 进列表 · ← 回类目 · Enter 插入 · Esc 取消", dim)
        self.put(2, 0, "─" * (width - 1))

        left_w = min(24, max(16, width // 5))
        right_w = max(10, width - left_w - 3)
        rows = max(len(self.cats), max((len(cat["items"]) for cat in self.cats), default=0))
        start = 3

        for i in range(rows):
            if i < len(self.cats):
                cat = self.cats[i]
                selected = i == self.cat_index
                active = selected and self.col == 0
                count = str(len(cat["items"]))
                name = fit(("▸ " if selected else "  ") + cat["name"], left_w - len(count) - 1)
                line = name + " " * max(1, left_w - text_width(name) - len(count)) + count
                attr = accent if active else (curses.A_BOLD if selected else 0)
                self.put(start + i, 0, line, attr)

            if i < len(self.cat["items"]):
                item = self.cat["items"][i]
                selected = i == self.item_index
                active = selected and self.col == 1
                marker = "▸ " if selected else "  "
                author = f" · {item['author']}"
                author_w = min(text_width(author), max(8, right_w // 3))
                label_w = max(6, right_w - 2 - author_w)
                label = fit(" ".join(item["zh"].split()), label_w)
                line = marker + label + author
                attr = accent if active else (curses.A_BOLD if selected else dim)
                self.put(start + i, left_w + 3, line, attr)

        self.put(start + rows, 0, "─" * (width - 1))

        item = self.item
        y = start + rows + 1
        self.put(
            y,
            1,
            f"{item['id']} · {self.cat['name']} · "
            f"{ORIGIN.get(item['origin'], item['origin'])}"
            f"{' · 节选' if item.get('excerpt') else ''} · "
            f"{item['author']} · {item['date']}",
            meta,
        )
        y += 1
        self.put(y, 1, "中文", dim)
        y += 1
        for line in wrap(item["zh"], max(10, width - 3)):
            if y >= height - 2:
                break
            self.put(y, 1, line)
            y += 1
        if y < height - 2:
            self.put(y, 1, "原文", dim)
            y += 1
            en_lines = wrap(item["en"], max(10, width - 3))
            for line in en_lines[:2]:
                if y >= height - 2:
                    break
                self.put(y, 1, line, dim)
                y += 1
            if len(en_lines) > 2 and y < height - 2:
                self.put(y, 1, "…", dim)
                y += 1
        if y < height - 1:
            self.put(y, 1, item["url"], dim)

        screen.refresh()

    def read_key(self) -> int:
        key = self.screen.getch()
        if key != 27:
            return key
        self.screen.timeout(50)
        suffix = ""
        while len(suffix) < 2:
            nxt = self.screen.getch()
            if nxt == -1:
                break
            suffix += chr(nxt)
        self.screen.timeout(-1)
        return {
            "[A": curses.KEY_UP,
            "[B": curses.KEY_DOWN,
            "[C": curses.KEY_RIGHT,
            "[D": curses.KEY_LEFT,
            "OA": curses.KEY_UP,
            "OB": curses.KEY_DOWN,
            "OC": curses.KEY_RIGHT,
            "OD": curses.KEY_LEFT,
        }.get(suffix, 27)

    def run(self) -> tuple[dict | None, bool]:
        curses.curs_set(0)
        self.screen.keypad(True)
        try:
            curses.set_escdelay(1000)
        except AttributeError:
            pass
        self.init_colors()
        while True:
            self.draw()
            key = self.read_key()
            if key in (27, ord("q")):
                return None, True
            if key in (curses.KEY_UP, ord("k")):
                self.move(-1)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.move(1)
            elif key in (curses.KEY_LEFT, ord("h")):
                self.col = 0
            elif key in (curses.KEY_RIGHT, ord("l")):
                self.col = 1
            elif key in (10, 13, curses.KEY_ENTER):
                if self.col == 0:
                    self.col = 1
                else:
                    return self.item, False
            elif key == curses.KEY_RESIZE:
                continue


def main(argv: list[str] | None = None) -> int:
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--has-trigger", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.file)
    seed = path.read_text(encoding="utf-8")
    position = find_trigger(seed)

    if args.has_trigger:
        return 0 if position >= 0 else 1
    if position < 0:
        return 2

    before, after = seed[:position], seed[position + 2 :]
    item, cancelled = curses.wrapper(lambda screen: Picker(screen, load_cats()).run())
    if cancelled:
        path.write_text(before + after, encoding="utf-8")
    else:
        path.write_text(before + item["zh"] + after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
