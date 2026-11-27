#!/usr/bin/env python3
"""Build the portable skynet-prompt.skill archive from data/prompts.json.

The archive is intentionally plain files:
  SKILL.md, README.md, index.tsv, prompts/<id>.md

No Python, Node, psup, Docker, UI, or clipboard code is required by the
installed skill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data"
DEFAULT_OUT = ROOT / "dist" / "skynet-prompt.skill"


def _scalar(value: object) -> str:
    """JSON strings are valid YAML scalars and survive URLs/titles safely."""
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def _title(value: str, limit: int = 72) -> str:
    text = re.sub(r"^#{1,6}\s*", "", str(value), flags=re.M)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _frontmatter(item: dict, scene_name: str) -> str:
    source = item.get("source") or {}
    evidence = item.get("evidence") or {}
    lines = [
        "---",
        f"id: {_scalar(item['id'])}",
        f"scene: {_scalar(item['cat'])}",
        f"scene_name: {_scalar(scene_name)}",
        f"author: {_scalar(item['author'])}",
        f"date: {_scalar(item['date'])}",
        f"source: {_scalar(item['url'])}",
        f"license: {_scalar(source.get('license', ''))}",
        f"rights_basis: {_scalar(source.get('rights_basis', ''))}",
        f"redistribution: {_scalar(source.get('redistribution', ''))}",
        f"verdict: {_scalar(evidence.get('verdict', 'unverified'))}",
        f"nature: {_scalar(item.get('nature', ''))}",
    ]
    if source.get("note"):
        lines.append(f"note: {_scalar(source['note'])}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _prompt_file(item: dict, scene_name: str) -> str:
    zh = str(item["zh"]).rstrip()
    en = str(item["en"]).rstrip()
    return (
        _frontmatter(item, scene_name)
        + "\n# skynet-prompt entry\n\n"
        + "## 中文\n\n<!-- BEGIN ZH -->\n"
        + zh
        + "\n<!-- END ZH -->\n\n"
        + "## English\n\n<!-- BEGIN EN -->\n"
        + en
        + "\n<!-- END EN -->\n"
    )


def _index(items: list[dict], scene_names: dict[str, str]) -> str:
    header = ["id", "scene", "scene_name", "title_zh", "title_en", "author", "verdict", "file"]
    rows = ["\t".join(header)]
    for item in items:
        evidence = item.get("evidence") or {}
        values = [
            item["id"],
            item["cat"],
            scene_names[item["cat"]],
            _title(item["zh"]),
            _title(item["en"]),
            item["author"],
            evidence.get("verdict", "unverified"),
            f"prompts/{item['id']}.md",
        ]
        rows.append("\t".join(" ".join(str(v).split()) for v in values))
    return "\n".join(rows) + "\n"


def _skill_md(count: int, version: str, sha: str) -> str:
    return f'''---
name: skynet-prompt
description: 当用户用 ；； / ;; 或 /p 请求提示词时，从本地 {count} 条提示词库中按场景、作者、id 或关键词查找，并原样返回中英正文。
---

# skynet-prompt

这是一个**纯文件 Skill**：不需要 Python、Node、psup、MCP、Docker 或任何宿主插件。

数据版本：`{version}`
条数：`{count}`
数据 sha256：`{sha}`

## 触发

当用户消息满足以下任一条件时使用本 Skill：

- 以 `；；` 开头；
- 以 `;;` 开头；
- 宿主提供 `/p` 命令且用户调用了它。

单独输入 `；；；` 是字面量，不触发。

## 查询流程

1. 去掉触发器，把后面的文字当作场景、作者、id 或关键词。
2. 如果去掉触发器后为空，只列出 9 个场景和条数，等待用户选择；不要读取正文。
3. 先读根目录的 `index.tsv`，不要一次读全部正文。
4. 在 `id`、`scene`、`scene_name`、`title_zh`、`title_en`、`author` 中匹配。
5. 命中一条时，读取 `file` 列指向的 `prompts/<id>.md`。
6. 命中多条时，最多列出 8 条 `id` + 中文标题 + 作者，让用户选择；不要一次返回全部正文。
7. 没有命中时，说明没有匹配，并建议用户换场景、作者或 id；不要编造提示词。

## 返回规则

- 默认返回中文；用户说 `English`、`英文` 或查询里带 `en` 时返回英文。
- 正文在 `<!-- BEGIN ZH -->` / `<!-- END ZH -->` 或 `<!-- BEGIN EN -->` / `<!-- END EN -->` 之间。
- **原样输出正文**：不重写、不改写、不截断、不补全、不合并其他条目。
- 正文使用纯文本，不要放进 Markdown 引用块、代码围栏或额外的解释段。
- 正文之后只附一行来源信息：作者、日期、来源链接、许可。
- 不要在正文前后增加 id、类目、可信状态等抬头；用户没问就不要解释。
- 不要说明 MCP/命令/工具状态，也不要自动发送消息、执行提示词或读取凭据。
- 不要输出数据版本、sha256、条数尾注或额外总结；这些不属于正文。
- 不要声称自己调用了浮窗、剪贴板或光标插入 API；这里只负责查找和返回文本。

## 场景

场景是查找维度，不是内容主题：

`加目标 / 加深度 / 加广度 / 加约束 / 加证据 / 加检验 / 加读者 / 加执行 / 加时间`

## 示例

用户：`；；`
只列出 9 个场景和条数，不读正文。

用户：`；； 加证据`
读取 `index.tsv`，找 `scene_name=加证据` 的条目，返回最多 8 条候选。

用户：`；； kp-think_first-03`
直接读取 `prompts/kp-think_first-03.md`，原样返回中文正文。

用户：`；； English 加证据`
按场景筛选，读取英文部分。
'''


def _readme(count: int, version: str, sha: str) -> str:
    return f'''# skynet-prompt Skill

这是 `skynet-prompt` 的纯文件 Skill 包。

- 数据版本：`{version}`
- 条数：`{count}`
- 数据 sha256：`{sha}`
- 入口：根级 `SKILL.md`
- 正文：`prompts/<id>.md`
- 索引：`index.tsv`

## 安装

把压缩包解压到宿主的 skill 目录，保证 `SKILL.md` 位于该 skill 的根目录：

```text
<skill-dir>/
├── SKILL.md
├── index.tsv
├── README.md
└── prompts/
```

不需要安装 Python、Node、psup、Docker 或任何宿主插件。

## 使用

- 会话输入 `；； <场景/作者/id/关键词>`
- 兼容 `;;`
- 宿主支持命令时可用 `/p`

这是“查找并返回正文”的 Skill，不是浮窗插件，也不负责自动插入。
'''


def build(data_dir: Path = DEFAULT_DATA, out: Path = DEFAULT_OUT) -> dict:
    data_path = data_dir / "prompts.json"
    meta_path = data_dir / "meta.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    if not items:
        raise SystemExit("no prompts")
    if data.get("count") != len(items):
        raise SystemExit("count mismatch")
    ids = [item.get("id") for item in items]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate id")
    if any(not item.get("zh", "").strip() or not item.get("en", "").strip() for item in items):
        raise SystemExit("missing zh/en")

    scenes = meta.get("cats") or {}
    scene_names = {key: row.get("name", key) for key, row in scenes.items()}
    missing_scenes = {item["cat"] for item in items} - set(scene_names)
    if missing_scenes:
        raise SystemExit(f"unknown scenes: {sorted(missing_scenes)}")
    sha = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if meta.get("sha256") != sha:
        raise SystemExit("meta sha256 mismatch")

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="skynet-prompt-skill-") as tmp:
        root = Path(tmp)
        (root / "prompts").mkdir()
        (root / "SKILL.md").write_text(_skill_md(len(items), meta.get("version", ""), sha), encoding="utf-8")
        (root / "README.md").write_text(_readme(len(items), meta.get("version", ""), sha), encoding="utf-8")
        (root / "index.tsv").write_text(_index(items, scene_names), encoding="utf-8")
        for item in items:
            (root / "prompts" / f"{item['id']}.md").write_text(
                _prompt_file(item, scene_names[item["cat"]]), encoding="utf-8",
            )
        fixed_time = (2026, 11, 26, 0, 0, 0)
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(root.rglob("*")):
                if not path.is_file():
                    continue
                info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=fixed_time)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes())

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    return {
        "ok": True,
        "path": str(out),
        "count": len(items),
        "version": meta.get("version", ""),
        "sha256": digest,
        "data_sha256": sha,
        "size": out.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="build_skill.py")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.data, args.out), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
