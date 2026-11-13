"""Codex 外部编辑器抽屉的纯逻辑测试（不启动 curses）。"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PICKER = REPO / "adapters" / "codex-picker" / "picker.py"

spec = importlib.util.spec_from_file_location("codex_picker", PICKER)
picker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(picker)


def test_double_semicolon():
    assert picker.find_trigger("你好;;") == 2
    assert picker.find_trigger("ab;;cd") == 2
    assert picker.find_trigger(";;") == 0
    assert picker.find_trigger("你好；；") == 2
    assert picker.find_trigger("；；") == 0


def test_url_is_not_a_trigger():
    assert picker.find_trigger("http://example.com") == -1
    assert picker.find_trigger("see https://example.com") == -1


def test_selection_preserves_both_sides():
    assert picker.apply_selection("ab;;cd", "X") == "abXcd"
    assert picker.apply_selection("你好;;", "X") == "你好X"
    assert picker.apply_selection(";;", "X") == "X"
    assert picker.apply_selection("你好；；", "X") == "你好X"
    assert picker.apply_selection("http://x", "X") == "http://x"


def test_loads_all_items():
    cats = picker.load_cats()
    assert len(cats) == 9
    assert sum(len(cat["items"]) for cat in cats) == 42
    assert all(item["zh"] for cat in cats for item in cat["items"])
    names = {cat["key"]: cat["name"] for cat in cats}
    assert names["verify"] == "定验收"


def test_picker_files_are_executable():
    import os

    assert PICKER.exists()
    assert (REPO / "adapters" / "codex-picker" / "psup-editor.sh").exists()
    assert os.access(PICKER, os.X_OK)
    assert os.access(REPO / "adapters" / "codex-picker" / "psup-editor.sh", os.X_OK)
