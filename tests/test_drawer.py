"""抽屉的状态机与排版：不启终端，直接调 fragments()。"""

from __future__ import annotations

from skynet_prompt.drawer import Drawer, _at_second_semicolon, _cells


class FakeBuffer:
    """够用的替身：插入、前删、按光标位置删除。"""

    def __init__(self) -> None:
        self.text = ""
        self.cursor_position = 0

    def insert_text(self, text: str) -> None:
        i = self.cursor_position
        self.text = self.text[:i] + text + self.text[i:]
        self.cursor_position = i + len(text)

    def delete(self, count: int = 1) -> None:
        i = self.cursor_position
        self.text = self.text[:i] + self.text[i + count:]


def test_second_semicolon_triggers_after_text():
    assert _at_second_semicolon("你好；")
    assert _at_second_semicolon("你好;")
    assert not _at_second_semicolon("你好")
    assert not _at_second_semicolon("")


def make(columns: int = 120) -> Drawer:
    drawer = Drawer()
    drawer.open = True
    drawer._size = lambda: (columns, 40)   # 固定视口，排版可断言
    drawer.buffer = FakeBuffer()
    return drawer


def lines(drawer: Drawer) -> list[list[tuple[str, str]]]:
    out: list[list[tuple[str, str]]] = [[]]
    for style, text in drawer.fragments():
        for chunk in text.split("\n")[:-1] if text.endswith("\n") else [text]:
            out[-1].append((style, chunk))
        if text.endswith("\n"):
            out.append([])
    return [ln for ln in out if ln]


def flat(drawer: Drawer) -> list[str]:
    return ["".join(t for _s, t in ln) for ln in lines(drawer)]


def test_down_moves_category_and_resets_item():
    d = make()
    d.ci = 0
    d.ii = 2
    d.key_down()
    assert (d.ci, d.ii) == (1, 0)


def test_up_stops_at_first():
    d = make()
    d.key_up()
    assert d.ci == 0


def test_right_enters_items_and_down_moves_preview():
    d = make()
    d.key_down()                      # 第二类
    d.key_right()
    assert d.focus == "items"
    first = d.current()["zh"]
    d.key_down()
    assert d.current()["zh"] != first
    d.key_left()
    assert d.focus == "cats"


def test_preview_follows_category():
    d = make()
    d.ci = 0
    assert d.current()["cat"] == d.cats[0][1]
    d.ci = 3
    assert d.current()["cat"] == d.cats[3][1]
    rendered = "".join(flat(d))
    assert d.current()["en"][:20] in rendered


def test_typing_filters_the_whole_library():
    d = make()
    assert len(d.rows()) < len(d.items)          # 默认只看当前类
    for ch in "裁判":
        d.type_char(ch)
    assert d.query == "裁判"
    assert d.focus == "items"
    hits = d.rows()
    assert hits and all("裁判" in i["zh"] for i in hits)
    d.backspace()
    assert d.query == "裁"
    d.backspace()
    assert d.query == "" and d.focus == "cats"


def test_long_result_set_is_windowed():
    d = make()
    for ch in "e":                     # 英文原文里遍地是 e，命中远超一屏
        d.type_char(ch)
    assert len(d.rows()) > 10
    assert d.height() <= 2 + 10 + 1 + 8
    rendered = "".join(flat(d))
    assert "下面还有" in rendered
    for _ in range(len(d.rows()) - 1):     # 一路按到底，窗口要跟到末条
        d.key_down()
    assert d.current()["zh"][:10] in "".join(flat(d))


def test_search_renders_the_query_in_header():
    d = make()
    d.type_char("流失")
    text = "".join(flat(d))
    assert "搜索「流失」" in text


def test_undo_removes_the_inserted_slice_only():
    d = make()
    d.buffer.text = "先写个通知："
    d.buffer.cursor_position = len(d.buffer.text)
    d.key_right()
    want = d.current()["zh"]
    d.accept()
    assert d.buffer.text == "先写个通知：" + want
    assert d.last is not None
    d.undo()
    assert d.buffer.text == "先写个通知："
    assert d.last is None


def test_insert_adds_a_space_after_latin_text():
    d = make()
    d.buffer.text = "fix the bug"
    d.buffer.cursor_position = len(d.buffer.text)
    d.key_right()
    d.accept()
    assert d.buffer.text.startswith("fix the bug ")
    d.undo()
    assert d.buffer.text == "fix the bug"


def test_insert_does_not_add_space_after_chinese():
    d = make()
    d.buffer.text = "先说结论："
    d.buffer.cursor_position = len(d.buffer.text)
    d.key_right()
    d.accept()
    assert d.buffer.text.startswith("先说结论：")


def test_accept_inserts_zh_and_closes():
    d = make()
    d.key_down()
    d.key_right()
    d.key_down()
    want = d.current()["zh"]
    d.accept()
    assert d.buffer.text == want
    assert d.open is False


def test_every_line_fits_the_terminal():
    for columns in (80, 100, 120, 160):
        d = make(columns)
        for line in flat(d):
            assert _cells(line) <= columns, (columns, _cells(line), line)
        d.key_right()
        for line in flat(d):
            assert _cells(line) <= columns, (columns, _cells(line), line)


def test_category_rows_align():
    """分隔线要落在同一格上——中文占两格，按字符 index 量会假过。"""
    d = make()
    cols = [_cells(line.split("│")[0]) for line in flat(d)[2 : 2 + len(d.cats)]]
    assert len(set(cols)) == 1, cols
