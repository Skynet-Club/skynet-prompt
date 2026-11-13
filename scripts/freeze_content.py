#!/usr/bin/env python3
"""把 data/prompts.json 冻结成 content/ 下的逐条文件。

一次迁移，之后 content/ 是发布与构建真相源；data/ 仅作兼容镜像，脚本保留用于复核与重建。

    python3 scripts/freeze_content.py [--check]

`--check` 只比对、不写文件：现有 content/ 与 data/ 不一致时退出 1。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.content import item_digest  # noqa: E402

LEGACY = ROOT / "data"
CONTENT = ROOT / "content"

# evidence.verdict -> 对外唯一的出处类型
ORIGIN = {
    "verbatim": "verbatim",
    "paraphrase": "compilation",
    "unverified": "unverified",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def meta_for(item: dict) -> dict:
    verdict = (item.get("evidence") or {}).get("verdict", "unverified")
    if verdict not in ORIGIN:
        raise SystemExit(f"{item['id']}: 未知 evidence.verdict={verdict!r}")
    source = item.get("source") or {}
    return {
        "id": item["id"],
        "cat": item["cat"],
        "author": item["author"],
        "date": item["date"],
        "url": item["url"],
        "origin": ORIGIN[verdict],
        "excerpt": bool(item.get("excerpt")),
        "source": {
            "url": source.get("url", item["url"]),
            "author": source.get("author", item["author"]),
            "published_at": source.get("published_at", item["date"]),
            "license": source.get("license", "not-declared"),
            "rights_basis": source.get(
                "rights_basis", "short-quotation-with-attribution"
            ),
            "redistribution": source.get("redistribution", "excerpt-only"),
        },
        "sha256": {
            "zh": sha256(item["zh"].encode("utf-8")),
            "en": sha256(item["en"].encode("utf-8")),
        },
    }


def build(legacy_dir: Path = LEGACY) -> tuple[dict, dict[str, dict]]:
    payload = json.loads((legacy_dir / "prompts.json").read_text(encoding="utf-8"))
    meta = json.loads((legacy_dir / "meta.json").read_text(encoding="utf-8"))
    items = payload["items"]

    entries: list[dict] = []
    files: dict[str, dict] = {}
    for item in items:
        row = meta_for(item)
        files[row["id"]] = {"meta": row, "zh": item["zh"], "en": item["en"]}
        entries.append({
            "id": row["id"],
            "cat": row["cat"],
            "author": row["author"],
            "date": row["date"],
            "url": row["url"],
            "origin": row["origin"],
            "excerpt": row["excerpt"],
            "source": row["source"],
            "sha256": row["sha256"],
            "path": f"items/{row['id']}",
        })

    digest = item_digest(entries)
    origins = {name: 0 for name in ("verbatim", "compilation", "unverified")}
    rights: dict[str, int] = {}
    cats: dict[str, int] = {}
    for e in entries:
        origins[e["origin"]] += 1
        basis = e["source"]["rights_basis"]
        rights[basis] = rights.get(basis, 0) + 1
        cats[e["cat"]] = cats.get(e["cat"], 0) + 1

    index = {
        "schema_version": 2,
        "content_version": meta.get("version", payload.get("version", "")),
        "count": len(entries),
        "origins": origins,
        "rights": rights,
        "excerpts": sum(1 for e in entries if e["excerpt"]),
        "cats": cats,
        "cat_names": {k: v["name"] for k, v in meta.get("cats", {}).items()},
        "digest": digest,
        "items": entries,
    }
    return index, files


def write(index: dict, files: dict[str, dict], content_dir: Path) -> None:
    items_dir = content_dir / "items"
    items_dir.mkdir(parents=True, exist_ok=True)
    for item_id, data in files.items():
        target = items_dir / item_id
        target.mkdir(parents=True, exist_ok=True)
        (target / "zh.txt").write_bytes(data["zh"].encode("utf-8"))
        (target / "en.txt").write_bytes(data["en"].encode("utf-8"))
        (target / "meta.json").write_text(
            json.dumps(data["meta"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    (content_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def diff(index: dict, files: dict[str, dict], content_dir: Path) -> list[str]:
    problems: list[str] = []
    index_path = content_dir / "index.json"
    if not index_path.exists():
        return [f"缺少 {index_path}"]
    current = json.loads(index_path.read_text(encoding="utf-8"))
    if current != index:
        problems.append("index.json 与 data/ 重建结果不一致")
    for item_id, data in files.items():
        base = content_dir / "items" / item_id
        for name, text in (("zh.txt", data["zh"]), ("en.txt", data["en"])):
            path = base / name
            if not path.exists():
                problems.append(f"{item_id}: 缺少 {name}")
            elif path.read_bytes() != text.encode("utf-8"):
                problems.append(f"{item_id}: {name} 与 data/ 不一致")
        meta_path = base / "meta.json"
        if meta_path.exists():
            actual = json.loads(meta_path.read_text(encoding="utf-8"))
            if actual != data["meta"]:
                problems.append(f"{item_id}: meta.json 与 data/ 不一致")
        else:
            problems.append(f"{item_id}: 缺少 meta.json")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="只比对，不写文件")
    parser.add_argument("--content", type=Path, default=CONTENT)
    parser.add_argument("--legacy", type=Path, default=LEGACY)
    args = parser.parse_args()

    index, files = build(args.legacy)
    if args.check:
        problems = diff(index, files, args.content)
        print(json.dumps({
            "ok": not problems,
            "count": index["count"],
            "digest": index["digest"],
            "problems": problems,
        }, ensure_ascii=False))
        return 0 if not problems else 1

    write(index, files, args.content)
    print(json.dumps({
        "ok": True,
        "out": str(args.content),
        "count": index["count"],
        "origins": index["origins"],
        "excerpts": index["excerpts"],
        "digest": index["digest"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
