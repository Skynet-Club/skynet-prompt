"""补全器的单元测试：只喂 Document，不启动终端。

跑：python3 -m pytest tests -q
"""

from __future__ import annotations

from prompt_toolkit.document import Document

from skynet_prompt.menu import CATS, PromptMenuCompleter


def completions(text: str):
    doc = Document(text, len(text))
    return list(PromptMenuCompleter().get_completions(doc, None))


def test_two_semicolons_lists_nine_categories():
    rows = completions(";;")
    assert [r.display_text for r in rows] == [name for name, _ in CATS]
    assert [r.display_meta_text for r in rows] == [
        "2 条", "8 条", "5 条", "9 条", "4 条", "3 条", "6 条", "2 条", "3 条",
    ]
    # 选中一级只补全类目名，不能把 ;; 吃掉
    assert {r.text for r in rows} == {";;" + name for name, _ in CATS}


def test_full_width_semicolons_also_work():
    rows = completions("；；")
    assert [r.display_text for r in rows] == [name for name, _ in CATS]
    assert {r.text for r in rows} == {"；；" + name for name, _ in CATS}
    assert completions("；；定")[0].text == "；；定格式"


def test_trigger_after_text_preserves_prefix():
    rows = completions("你好；；")
    assert {r.text for r in rows} == {"；；" + name for name, _ in CATS}
    assert all(r.start_position == -2 for r in rows)

    rows = completions("你好；；定验收")
    assert rows[0].start_position == -len("；；定验收")
    # 应用补全时只替换 ;;定验收，不碰前面的“你好”
    before = "你好；；定验收"
    applied = before[: rows[0].start_position] + rows[0].text
    assert applied.startswith("你好")


def test_category_prefix_narrows():
    rows = completions(";;定")
    assert [r.display_text for r in rows] == ["定格式", "定验收"]


def test_category_shows_items_with_author():
    rows = completions(";;定验收")
    assert len(rows) == 9
    assert all(r.display_meta_text for r in rows)
    assert all(r.start_position == -len(";;定验收") for r in rows)


def test_item_insert_replaces_the_whole_token():
    rows = completions(";;定验收")
    row = rows[0]
    assert ";;" not in row.text
    assert len(row.text) > 4


def test_no_match_yields_nothing():
    assert completions(";;xyzzy") == []


def test_url_not_triggered():
    assert completions("https://example.com") == []
    assert completions("看这段 https://a.b/c") == []


def test_midline_comment_not_triggered():
    assert completions("看这段 ;; 注释") == []


def test_code_block_not_triggered():
    rows = PromptMenuCompleter().get_completions(Document("```\n;;", 5), None)
    assert list(rows) == []


def test_single_slash_not_triggered():
    assert completions("/") == []


def test_every_item_is_single_line():
    for name, key in CATS:
        for row in completions(";;" + name):
            assert "\n" not in row.text and row.text.strip()


def _with(tmp_path, payload):
    """把一份临时快照指给补全器用。"""
    import json
    import os

    old = os.environ.get("PROMPT_SUPPLEMENT_DATA")
    os.environ["PROMPT_SUPPLEMENT_DATA"] = str(tmp_path)
    (tmp_path / "prompts.json").write_text(json.dumps(payload, ensure_ascii=False))
    return old


def test_empty_category_is_not_listed(tmp_path):
    import os

    item = {"id": "x", "cat": "verify", "author": "Karpathy", "date": "2026-01-01",
            "url": "https://x.com/a", "en": "State assumptions.", "zh": "先说假设。"}
    old = _with(tmp_path, {"version": "t", "count": 1, "items": [item]})
    try:
        names = [r.display_text for r in completions(";;")]
        assert names == ["定验收"], names
    finally:
        if old is None:
            os.environ.pop("PROMPT_SUPPLEMENT_DATA", None)
        else:
            os.environ["PROMPT_SUPPLEMENT_DATA"] = old


def test_missing_snapshot_reports_and_yields_nothing(tmp_path):
    import os

    old = _with(tmp_path, {"version": "t", "count": 0, "items": []})
    try:
        assert completions(";;") == []
        from skynet_prompt.menu import get_completer
        assert get_completer() is None
    finally:
        if old is None:
            os.environ.pop("PROMPT_SUPPLEMENT_DATA", None)
        else:
            os.environ["PROMPT_SUPPLEMENT_DATA"] = old

