"""端到端：真的 prompt_toolkit 会话，真的按键。

跑：/path/to/hermes-venv/python3 tests/test_session.py
断言三件（TC-01/03/04/05）：;; 出九类 → 打「定验收」出 9 条 → 选中把 ;;定验收
整段换成中文直译、其余文字不变、光标在末尾、**没有提交**。
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prompt_toolkit import PromptSession  # noqa: E402
from prompt_toolkit.completion import ThreadedCompleter  # noqa: E402
from prompt_toolkit.input import create_pipe_input  # noqa: E402
from prompt_toolkit.output import DummyOutput  # noqa: E402

from skynet_prompt.menu import PromptMenuCompleter  # noqa: E402


def wait_for(predicate, label: str, timeout: float = 5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.02)
    raise AssertionError(f"等不到：{label}")


def run() -> int:
    results: dict[str, str] = {}
    with create_pipe_input() as pipe:
        session = PromptSession(
            message="> ",
            input=pipe,
            output=DummyOutput(),
            completer=ThreadedCompleter(PromptMenuCompleter()),
            complete_while_typing=True,
            multiline=True,
        )

        def app():
            try:
                results["submitted"] = session.prompt()
            except BaseException as exc:  # noqa: BLE001
                results["error"] = repr(exc)

        thread = threading.Thread(target=app, daemon=True)
        thread.start()
        buf = session.default_buffer
        wait_for(lambda: session.app.is_running, "启动")

        pipe.send_text(";;")
        state = wait_for(
            lambda: buf.complete_state if (
                buf.complete_state and len(buf.complete_state.completions) == 9) else None,
            "一级菜单")
        rows = list(state.completions)
        assert [c.display_text for c in rows] == [
            "要结果", "先想清楚", "定格式", "定验收", "换视角",
            "用高手的方法", "换形态", "砍掉多余的", "别碰旁边的",
        ], [c.display_text for c in rows]
        assert rows[3].display_meta_text == "9 条"
        print(f"TC-01 PASS  ;; → {len(rows)} 类，定验收右侧 {rows[3].display_meta_text}")

        pipe.send_text("定验收")
        state = wait_for(
            lambda: buf.complete_state if (
                buf.complete_state
                and len(buf.complete_state.completions) == 9
                and not any(
                    c.display_meta_text.endswith("条")
                    for c in buf.complete_state.completions
                )
            ) else None,
            "二级菜单")
        rows = list(state.completions)
        assert all(c.display_meta_text for c in rows), "每条都要带作者"
        print(f"TC-03 PASS  ;;定验收 → {len(rows)} 条，首条 {rows[0].display_text} / {rows[0].display_meta_text}")

        target = rows[0].text
        pipe.send_text("\x1b[B")          # ↓ 选中第一条
        time.sleep(0.1)
        pipe.send_text("\r")               # Enter：应用补全，不是提交
        wait_for(lambda: buf.text == target, "整段替换")
        assert ";;" not in buf.text, buf.text
        assert buf.document.cursor_position == len(buf.text), "光标要在末尾"
        assert not results.get("submitted"), "选中后不得自动发送"
        print(f"TC-04 PASS  替换成：{buf.text[:40]}…")
        print("TC-05 PASS  未提交、光标在末尾")

        # 提交键由宿主绑定（Hermes 里 Enter 提交）；这里只证明补全本身不提交，
        # 见上面的 assert not results.get("submitted")。

    print("\nSESSION 全过")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("FAIL", exc)
        sys.exit(1)
