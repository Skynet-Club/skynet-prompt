"""从 content/ 生成宿主产物（pi、codex）。

原则：生成物里的正文就是 content/items/<id>/zh.txt 的字节，不加前缀、不折行、
不补结尾换行。元数据只进 frontmatter / manifest，不进正文。
"""

from __future__ import annotations

import json
from pathlib import Path

from . import __version__
from .catalog import DISPLAY
from .content import CONTENT, ORIGIN_LABELS, load_item
from .trigger import ASCII_TRIGGER, CANONICAL_TRIGGER, LITERAL_ESCAPE

REPO = Path(__file__).resolve().parent.parent
VERSION = __version__
HOSTS = ("pi", "codex", "opencode")


def slug(item_id: str) -> str:
    return item_id.replace("_", "-")


def load_items(content_root: Path | str = CONTENT) -> list[dict]:
    root = Path(content_root)
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    return [load_item(root, entry["id"]) for entry in index["items"]]


def description(item: dict) -> str:
    head = " ".join(item["zh"].split())
    if len(head) > 36:
        head = head[:36] + "…"
    parts = [
        "中文直译",
        DISPLAY.get(item["cat"], item["cat"]),
        ORIGIN_LABELS[item["origin"]],
    ]
    if item["excerpt"]:
        parts.append("节选")
    parts.append(head)
    return " · ".join(parts)


def _frontmatter(fields: dict) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def pi_prompt(item: dict) -> bytes:
    body = _frontmatter({"description": description(item)}) + item["zh"]
    return body.encode("utf-8")


def codex_skill(item: dict) -> bytes:
    body = _frontmatter({
        "name": "psup-" + slug(item["id"]),
        "description": description(item),
        "disable-model-invocation": True,
    }) + item["zh"]
    return body.encode("utf-8")


def psup_skill(items: list[dict]) -> bytes:
    lines = [
        "---",
        'name: "psup"',
        f'description: "当用户消息以 {CANONICAL_TRIGGER}（兼容 {ASCII_TRIGGER}）开头时：消息里还没有类目，运行 psup categories --json，只列 9 个类目和条数并停下；已有类目，直接运行 psup list --category <key> --json，只列该类条目并停下；已有条目 id，运行 psup print <id>，把输出原样放到当前任务末尾。不要一次列出全部条目。"',
        "---",
        "",
        "# skynet-prompt",
        "",
        f"当用户消息以 `{CANONICAL_TRIGGER}` 或兼容的 `{ASCII_TRIGGER}` 开头时，"
        "去掉触发器，把后面的文字当作类目、搜索词或条目 id。",
        f"单独输入 `{LITERAL_ESCAPE}` 时保留字面量 `{CANONICAL_TRIGGER}`，不要调用工具。",
        "",
        "状态判断：",
        "- 用户消息里没有类目：运行 `psup categories --json`，只列 9 个类目和条数，停下。",
        "- 用户消息里已有类目（名称或 key）：直接运行 `psup list --category <key> --json`，只列该类条目，不要再列类目。",
        "- 用户已经给出条目 id：运行 `psup print <id>`，把输出原样放到当前任务末尾；不要改写、截断或加前缀。",
        "",
        "如果 `psup` 在 PATH 里，严格按上面执行。下面的完整索引只在 `psup` 不可用时使用；同样先只列类目，不要一次列全部。",
        "",
    ]
    for key, name in DISPLAY.items():
        rows = [item for item in items if item["cat"] == key]
        lines.append(f"## {name}（{len(rows)}）")
        lines.append("")
        for item in rows:
            tags = [item["author"], ORIGIN_LABELS[item["origin"]]]
            if item["excerpt"]:
                tags.append("节选")
            lines.append(f"### {item['id']}")
            lines.append("作者：" + " · ".join(tags))
            lines.append("中文：" + item["zh"])
            lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def opencode_command(item: dict) -> bytes:
    body = _frontmatter({"description": description(item)}) + item["zh"]
    return body.encode("utf-8")


def pi_readme(count: int) -> str:
    return f"""# Pi 产物（{count} 条）

由 `psup build` 从 `content/` 生成，不要手改。

## 安装

```sh
pi install git:github.com/<owner>/skynet-prompt@v1
```

或本地试用：

```sh
pi install /path/to/skynet-prompt
```

## 使用

输入 `；；` 打开抽屉，或输入 `/psup-` 过滤出全部条目，例如：

```text
/psup-kp-verify-18
```

正文是中文直译，逐字节来自 `content/items/<id>/zh.txt`。要英文原文：

```sh
psup print kp-verify-18 --field en
```

菜单描述里的 `本人原话 / 他人整理 / 未核实 / 节选` 是出处标记，不是正文。
"""


def opencode_readme(count: int) -> str:
    return f"""# opencode 产物（{count} 条）

由 `psup build` 从 `content/` 生成，不要手改。

## 安装

```sh
mkdir -p ~/.config/opencode/command
cp adapters/opencode/commands/psup-*.md ~/.config/opencode/command/
```

## 使用

当前输入框入口是 `/psup` 或 `/prompts`。统一触发器 `；；` 在该宿主暂无原生拦截，
因此会走文本指令或命令降级；也可以 `/psup-<id>` 直接取单条。

正文是中文直译，逐字节来自 `content/items/<id>/zh.txt`。要英文原文：

```sh
psup print kp-verify-18 --field en
```

菜单描述里的 `本人原话 / 他人整理 / 未核实 / 节选` 是出处标记，不是正文。
"""


def codex_readme(count: int) -> str:
    return f"""# Codex 产物（{count} 条）

由 `psup build` 从 `content/` 生成，不要手改。

## 安装

```sh
codex plugin marketplace add <owner>/skynet-prompt
codex plugin add skynet-prompt@skynet-prompt
```

## 使用

输入 `；；` → 只列 9 个类目；回复类目 → 只列该类条目；回复 id → 原样正文。

```text
；；
；； 先想清楚
；； kp-think_first-03
```

也可以直接用 `$psup-<id>` 取单条。

Codex 的显式技能兼容入口仍然可用：

```text
$psup
$psup-kp-verify-18
```

也可以输入 `$` 打开技能列表，或用 `/skills` → List skills。

每个 skill 的正文是中文直译，逐字节来自 `content/items/<id>/zh.txt`；
单条 skill 使用 `disable-model-invocation: true`，只能显式选择；索引 skill 由统一
触发器激活，不会被普通请求自动挑中。
菜单描述里的 `本人原话 / 他人整理 / 未核实 / 节选` 是出处标记，不是正文。

要英文原文：

```sh
psup print kp-verify-18 --field en
```
"""


def render(content_root: Path | str = CONTENT) -> dict[str, bytes]:
    items = load_items(content_root)
    names = [slug(item["id"]) for item in items]
    if len(set(names)) != len(names):
        raise SystemExit("生成的命令名有重复，检查 id 里的 _ 与 -")

    files: dict[str, bytes] = {}
    files["package.json"] = (
        json.dumps({
            "name": "skynet-prompt",
            "version": VERSION,
            "description": "42 条带出处与中文直译的提示词，供 AI Agent 原样检索和插入",
            "license": "MIT",
            "keywords": ["pi-package", "prompts", "agents"],
            "pi": {
                "prompts": ["./adapters/pi/prompts/*.md"],
                "extensions": ["./adapters/pi-extension/index.ts"],
            },
        }, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    files[".agents/plugins/marketplace.json"] = (
        json.dumps({
            "name": "skynet-prompt",
            "interface": {"displayName": "Skynet Prompt"},
            "plugins": [{
                "name": "skynet-prompt",
                "source": {"source": "local", "path": "./adapters/codex-plugin"},
                "policy": {"installation": "AVAILABLE", "products": ["CODEX"]},
                "category": "Developer Tools",
            }],
        }, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    files["adapters/pi/README.md"] = pi_readme(len(items)).encode("utf-8")
    files["adapters/codex-plugin/README.md"] = codex_readme(len(items)).encode("utf-8")
    files["adapters/opencode/commands/README.md"] = opencode_readme(len(items)).encode("utf-8")

    for item in items:
        name = slug(item["id"])
        files[f"adapters/pi/prompts/psup-{name}.md"] = pi_prompt(item)
        files[f"adapters/codex-plugin/skills/psup-{name}/SKILL.md"] = codex_skill(item)
        files[f"adapters/opencode/commands/psup-{name}.md"] = opencode_command(item)

    files["adapters/codex-plugin/skills/psup/SKILL.md"] = psup_skill(items)

    files["adapters/codex-plugin/.codex-plugin/plugin.json"] = (
        json.dumps({
            "name": "skynet-prompt",
            "version": VERSION,
            "description": "32 条带出处与中文直译的提示词，选中即原样插入",
            "license": "MIT",
            "keywords": ["prompts", "chinese", "agents"],
            "skills": "./skills/",
            "interface": {
                "displayName": "Skynet Prompt",
                "shortDescription": "中文直译的大神提示词",
                "longDescription": "32 条提示词，带作者、日期、链接与出处类型；正文逐字节冻结。",
                "developerName": "skynet-prompt",
                "category": "Developer Tools",
                "capabilities": ["Read"],
            },
        }, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    return files


def _host_files(files: dict[str, bytes], hosts: tuple[str, ...]) -> dict[str, bytes]:
    selected: dict[str, bytes] = {}
    if "pi" in hosts:
        selected["package.json"] = files["package.json"]
    if "codex" in hosts:
        selected[".agents/plugins/marketplace.json"] = files[".agents/plugins/marketplace.json"]
    for path, data in files.items():
        if "pi" in hosts and path.startswith("adapters/pi/"):
            selected[path] = data
        if "codex" in hosts and path.startswith("adapters/codex-plugin/"):
            selected[path] = data
        if "opencode" in hosts and path.startswith("adapters/opencode/commands/"):
            selected[path] = data
    return selected


def _extras(root: Path, files: dict[str, bytes], hosts: tuple[str, ...]) -> list[str]:
    extras: list[str] = []
    if "pi" in hosts:
        prompts = root / "adapters" / "pi" / "prompts"
        if prompts.is_dir():
            for path in prompts.glob("*.md"):
                rel = str(path.relative_to(root))
                if rel not in files:
                    extras.append(rel)
    if "codex" in hosts:
        skills = root / "adapters" / "codex-plugin" / "skills"
        if skills.is_dir():
            for path in skills.glob("*/SKILL.md"):
                rel = str(path.relative_to(root))
                if rel not in files:
                    extras.append(rel)
    if "opencode" in hosts:
        commands = root / "adapters" / "opencode" / "commands"
        if commands.is_dir():
            for path in commands.glob("*.md"):
                rel = str(path.relative_to(root))
                if rel not in files:
                    extras.append(rel)
    return sorted(extras)


def check(repo_root: Path | str = REPO, hosts: tuple[str, ...] = HOSTS,
          content_root: Path | str = CONTENT) -> dict:
    root = Path(repo_root)
    expected = _host_files(render(content_root), hosts)
    missing, different = [], []
    for rel, data in expected.items():
        path = root / rel
        if not path.exists():
            missing.append(rel)
        elif path.read_bytes() != data:
            different.append(rel)
    extras = _extras(root, expected, hosts)
    problems = missing + different + extras
    return {
        "ok": not problems,
        "hosts": list(hosts),
        "expected": len(expected),
        "missing": missing,
        "different": different,
        "extra": extras,
    }


def build(repo_root: Path | str = REPO, hosts: tuple[str, ...] = HOSTS,
          content_root: Path | str = CONTENT) -> dict:
    root = Path(repo_root)
    expected = _host_files(render(content_root), hosts)
    missing, different = [], []
    written = 0
    for rel, data in expected.items():
        path = root / rel
        if path.exists() and path.read_bytes() == data:
            continue
        if not path.exists():
            missing.append(rel)
        else:
            different.append(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        written += 1
    removed = []
    for rel in _extras(root, expected, hosts):
        (root / rel).unlink()
        removed.append(rel)
    return {
        "ok": True,
        "hosts": list(hosts),
        "expected": len(expected),
        "written": written,
        "added": missing,
        "changed": different,
        "removed": removed,
    }
