#!/usr/bin/env python3
"""把已审核 Pack v2 导出为 Club 频道逐条发布稿件。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render(item: dict) -> str:
    verdict = "逐字可核" if item["evidence"]["verdict"] == "verbatim" else "他人整理"
    return (
        f"[提示词] `{item['id']}`\n"
        f"作者：{item['author']} · {item['date']}\n"
        f"性质：{verdict}\n"
        f"来源：{item['source']['url']}\n"
        f"版权：未声明可复用许可；短引用并保留署名与链接\n\n"
        f"原文（短引用）：{clip(item['en'], 260)}\n\n"
        f"中文直译：\n{item['zh']}\n\n"
        f"Pack：`{item['_pack_id']}@{item['_pack_version']}` · "
        f"快照：`{item['source']['snapshot_sha256'][:16]}…`"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--channel", default="13")
    args = parser.parse_args()

    manifest = json.loads((args.release / "pack.json").read_text(encoding="utf-8"))
    payload = json.loads((args.release / "prompts.json").read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    posts = []
    for item in payload["items"]:
        row = {
            **item,
            "_pack_id": manifest["id"],
            "_pack_version": manifest["version"],
        }
        text = render(row)
        path = args.out / f"{item['id']}.md"
        path.write_text(text + "\n", encoding="utf-8")
        posts.append({
            "id": item["id"],
            "author": item["author"],
            "date": item["date"],
            "source": item["source"]["url"],
            "nature": item["evidence"]["verdict"],
            "license": item["source"]["license"],
            "text": str(path),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })
    batch = {
        "schema_version": 1,
        "channel": args.channel,
        "pack_id": manifest["id"],
        "pack_version": manifest["version"],
        "pack_sha256": manifest["digest"],
        "count": len(posts),
        "posts": posts,
    }
    (args.out / "batch.json").write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "channel": args.channel,
        "count": len(posts),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
