"""把 9 个类目（或全部条目）导出成各家宿主的斜杠命令文件。

    python3 scripts/export_commands.py --target codex --out adapters/codex
    python3 scripts/export_commands.py --target claude --out adapters/claude
    python3 scripts/export_commands.py --target opencode --out adapters/opencode

生成的是"薄壳"：每个文件只干一件事——让宿主去调用 psup。**不复制数据**。
所以数据更新后不用重新导出；命令文件只在类目改名时才需要重跑。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PSUP = ROOT / "psup"

BODY = """按下面三步做，别自己编内容：

1. 运行 `psup {name}`，把命中的条目原样列给我（id / 类目 / 中文 / 作者）。
2. 等我选一条，然后用 `psup print <id>` 取它的中文直译。
3. 把取到的中文原样放在我这条需求的末尾，不要改写、不要截断、不要加"补充："之类的前缀；
   同时告诉我补的是哪一条（类目 + 标题），以及可以撤销。

如果 `psup` 不在 PATH 里，先运行 `python3 {install}`，再重试。
引用时保留作者与链接（`psup show <id>` 里有）。
"""

OPENCODE_BODY = """这是 opencode 的聊天式选择流程，不是二级原生菜单。不要假装弹出了不存在的子菜单。

1. 调用 `skynet-prompt` MCP 工具 `prompt_search`，参数
   `{{"category":"{name}","limit":200}}`。
2. 按 1、2、3… 编号展示结果：`id`、中文文本、作者、可信状态。不要改写中文。
3. 展示后停下来等我选择，不要自动应用。
4. 我选定后，调用 `prompt_get` 取该 `id`；把返回的 `zh` 原样作为我当前任务的附加约束。
   不改写、不截断、不加“补充：”，并说明条目 id、作者、来源和可以撤销。

如果 MCP 工具不可用，才退回到 `psup {name}` 和 `psup print <id>`。
"""

OPENCODE_BROWSE = """使用 `skynet-prompt` MCP 工具浏览全库：

1. 调用 `prompt_search`，参数 `{"limit":200}`。
2. 按 9 个类目分组，用编号展示每条的 `id`、中文、作者和可信状态。
3. 展示后停下来等用户按编号或 id 选择，不要自动应用。
4. 用户选择后调用 `prompt_get`，把 `zh` 原样作为当前任务的附加约束，并说明来源与撤销。

不要生成新提示词，也不要把 paraphrase 或 unverified 说成作者原话。
"""


def categories() -> list[tuple[str, str, int]]:
    meta = json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8"))
    return [(v["name"], k, v["count"]) for k, v in meta["cats"].items() if v["count"]]


def render(target: str, name: str, key: str, count: int) -> str:
    body = BODY.format(name=name, install=ROOT / "scripts" / "install.py")
    if target == "codex":
        # ~/.codex/prompts/<name>.md：frontmatter 只有 description，正文即提示词
        return f"---\ndescription: 提示词补充 · {name}（{count} 条）\n---\n\n{body}"
    if target == "claude":
        # ~/.claude/commands/<name>.md：frontmatter description + argument-hint
        return f"---\ndescription: 提示词补充 · {name}（{count} 条）\nargument-hint: [关键词]\n---\n\n{body}"
    if target == "opencode":
        # .opencode/command/<name>.md：description + template
        body = OPENCODE_BODY.format(name=name)
        return f"---\ndescription: 提示词补充 · 浏览 {name}（{count} 条）\n---\n\n{body}"
    raise SystemExit(f"不认识的 target: {target}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, choices=["codex", "claude", "opencode"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--all", action="store_true", help="同时导出每一条（32 个文件），默认只导类目")
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written = 0
    for name, key, count in categories():
        path = out / f"{name}.md"
        path.write_text(render(args.target, name, key, count), encoding="utf-8")
        written += 1
    if args.target == "opencode":
        (out / "psup.md").write_text(
            f"---\ndescription: 浏览 skynet-prompt 全库并选择条目\n---\n\n{OPENCODE_BROWSE}",
            encoding="utf-8",
        )
        written += 1
    if args.all:
        items = json.loads((ROOT / "data" / "prompts.json").read_text(encoding="utf-8"))["items"]
        for item in items:
            if args.target == "opencode":
                text = (
                    f"---\ndescription: {item['id']} · {item['author']}\n---\n\n"
                    f"调用 `skynet-prompt` MCP 工具 `prompt_get`，参数 "
                    f"`{{\"id\":\"{item['id']}\"}}`。把返回的 `zh` 原样作为我当前任务的"
                    f"附加约束，不改写；说明 id、作者、来源和可以撤销。\n"
                )
            else:
                text = (
                    f"---\ndescription: {item['id']} · {item['author']}\n---\n\n"
                    f"运行 `psup print {item['id']}`，把输出原样放到我这条需求的末尾；"
                    f"不要改写。然后告诉我补的是 {item['id']}（{item['author']}）。\n"
                )
            (out / f"{item['id']}.md").write_text(text, encoding="utf-8")
            written += 1

    index = out / "README.md"
    index.write_text(
        f"# {args.target} 命令文件（{written} 个）\n\n"
        f"由 `scripts/export_commands.py --target {args.target}` 生成。\n\n"
        "拷到宿主自己的命令目录即可：\n\n"
        "| 宿主 | 目录 |\n|---|---|\n"
        "| Claude Code | `~/.claude/commands/` |\n"
        "| Codex | `~/.codex/prompts/` |\n"
        "| opencode | `.opencode/command/` 或 `~/.config/opencode/command/` |\n\n"
        "这些文件不含数据，只调用 `psup`；发布快照在 `content/`，`data/` 仅作兼容镜像。\n",
        encoding="utf-8")
    print(f"{args.target}: 写出 {written} 个文件 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
