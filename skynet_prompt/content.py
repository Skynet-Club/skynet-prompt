"""content/ 内容层：逐条文件、sha256 与迁移一致性校验。

content/ 是发布与构建真相源；data/ 仅在迁移期作为兼容镜像：

    content/index.json
    content/items/<id>/zh.txt
    content/items/<id>/en.txt
    content/items/<id>/meta.json

文本文件就是正文字节，不折行、不规范化、不加前后缀。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .catalog import DISPLAY

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
LEGACY = REPO / "data"

ORIGINS = ("verbatim", "compilation", "unverified")
ORIGIN_LABELS = {
    "verbatim": "本人原话",
    "compilation": "他人整理",
    "unverified": "未核实",
}
REQUIRED_META = (
    "id", "cat", "author", "date", "url", "origin", "excerpt", "source", "sha256",
)
REQUIRED_SOURCE = (
    "url", "author", "published_at", "license", "rights_basis", "redistribution",
)


class ContentError(RuntimeError):
    """content/ 缺失、损坏或与迁移结果不一致。"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def item_digest(entries: list[dict]) -> str:
    """按 id 排序的稳定摘要，包含正文、出处、版权与性质字段。"""
    body = ""
    for entry in sorted(entries, key=lambda e: e["id"]):
        source = json.dumps(
            entry["source"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        body += (
            f"{entry['id']}\t{entry['sha256']['zh']}\t{entry['sha256']['en']}\t"
            f"{entry['origin']}\t{entry['excerpt']}\t{source}\n"
        )
    return sha256_bytes(body.encode("utf-8"))


def _read_json(path: Path, label: str) -> dict:
    if not path.exists():
        raise ContentError(f"{label}缺失：{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContentError(f"{label}损坏：{path}（{exc}）") from exc
    if not isinstance(payload, dict):
        raise ContentError(f"{label}格式错误：顶层必须是对象（{path}）")
    return payload


def load_item(root: Path, item_id: str) -> dict:
    """读一条，返回 meta + zh/en 文本，并校验 sha256。"""
    base = root / "items" / item_id
    meta = _read_json(base / "meta.json", f"{item_id} 的 meta")
    texts = {}
    for field in ("zh", "en"):
        path = base / f"{field}.txt"
        if not path.exists():
            raise ContentError(f"{item_id} 缺少 {field}.txt")
        data = path.read_bytes()
        texts[field] = data.decode("utf-8")
        declared = (meta.get("sha256") or {}).get(field)
        if declared != sha256_bytes(data):
            raise ContentError(f"{item_id} 的 {field}.txt sha256 不匹配")
    return {**meta, **texts, "path": base}


def _verify_meta(item_id: str, meta: dict, base: Path, errors: list[str]) -> dict | None:
    missing = [key for key in REQUIRED_META if key not in meta]
    if missing:
        errors.append(f"{item_id}: meta 缺少字段 {', '.join(missing)}")
        return None
    if meta["id"] != item_id:
        errors.append(f"{item_id}: meta.id={meta['id']!r} 与目录名不一致")
    if meta["cat"] not in DISPLAY:
        errors.append(f"{item_id}: 未知类目 {meta['cat']!r}")
    if meta["origin"] not in ORIGINS:
        errors.append(f"{item_id}: 未知 origin {meta['origin']!r}")
    if not isinstance(meta["excerpt"], bool):
        errors.append(f"{item_id}: excerpt 必须是布尔值")
    source = meta["source"]
    if not isinstance(source, dict):
        errors.append(f"{item_id}: source 必须是对象")
    else:
        missing_source = [key for key in REQUIRED_SOURCE if not source.get(key)]
        if missing_source:
            errors.append(f"{item_id}: source 缺少字段 {', '.join(missing_source)}")
        if source.get("url") != meta.get("url"):
            errors.append(f"{item_id}: source.url 与 url 不一致")
    for field in ("zh", "en"):
        path = base / f"{field}.txt"
        if not path.exists():
            errors.append(f"{item_id}: 缺少 {field}.txt")
            continue
        actual = sha256_bytes(path.read_bytes())
        declared = (meta.get("sha256") or {}).get(field)
        if declared != actual:
            errors.append(
                f"{item_id}: {field}.txt sha256 不匹配（声明 {declared}，实际 {actual}）"
            )
    return {
        "id": meta["id"],
        "cat": meta["cat"],
        "author": meta["author"],
        "date": meta["date"],
        "url": meta["url"],
        "origin": meta["origin"],
        "excerpt": meta["excerpt"],
        "source": source,
        "sha256": meta["sha256"],
        "path": f"items/{item_id}",
    }


def verify(root: Path | str = CONTENT, legacy: Path | str = LEGACY) -> dict:
    """只读校验 content/，可选与 data/ 做逐字节迁移比对。"""
    root = Path(root)
    legacy = Path(legacy)
    errors: list[str] = []
    index = _read_json(root / "index.json", "内容索引")
    entries = index.get("items")
    if not isinstance(entries, list) or not entries:
        raise ContentError(f"内容索引没有条目：{root / 'index.json'}")

    declared = [e.get("id") for e in entries if isinstance(e, dict)]
    if len(set(declared)) != len(declared):
        errors.append("index.json 里有重复 id")

    rebuilt: list[dict] = []
    for entry in entries:
        item_id = entry.get("id", "")
        base = root / "items" / item_id
        if not base.is_dir():
            errors.append(f"{item_id}: 条目目录缺失 {base}")
            continue
        try:
            meta = _read_json(base / "meta.json", f"{item_id} 的 meta")
        except ContentError as exc:
            errors.append(str(exc))
            continue
        row = _verify_meta(item_id, meta, base, errors)
        if row is None:
            continue
        for key in (
            "cat", "author", "date", "url", "origin", "excerpt",
            "source", "sha256", "path",
        ):
            if entry.get(key) != row[key]:
                errors.append(f"{item_id}: index.{key} 与 meta 不一致")
        rebuilt.append(row)

    on_disk = {p.name for p in (root / "items").iterdir() if p.is_dir()} if (root / "items").is_dir() else set()
    for extra in sorted(on_disk - set(declared)):
        errors.append(f"{extra}: 目录不在 index.json 里")
    for missing in sorted(set(declared) - on_disk):
        errors.append(f"{missing}: index.json 有记录但目录不存在")

    if index.get("count") != len(entries):
        errors.append(f"index.count={index.get('count')} 与条目数 {len(entries)} 不一致")

    origins = {name: 0 for name in ORIGINS}
    for row in rebuilt:
        origins[row["origin"]] = origins.get(row["origin"], 0) + 1
    excerpts = sum(1 for row in rebuilt if row["excerpt"])
    digest = item_digest(rebuilt)

    if index.get("digest") != digest:
        errors.append(f"index.digest 不匹配：声明 {index.get('digest')}，实际 {digest}")
    if index.get("origins") != origins:
        errors.append(f"index.origins 不匹配：声明 {index.get('origins')}，实际 {origins}")
    if index.get("excerpts") != excerpts:
        errors.append(f"index.excerpts 不匹配：声明 {index.get('excerpts')}，实际 {excerpts}")

    legacy_state = "absent"
    if (legacy / "prompts.json").exists():
        legacy_state = "match"
        try:
            payload = _read_json(legacy / "prompts.json", "旧数据文件")
            old_items = {item["id"]: item for item in payload["items"]}
        except (ContentError, KeyError, TypeError) as exc:
            legacy_state = "mismatch"
            errors.append(f"旧数据无法读取：{exc}")
            old_items = {}
        if old_items:
            for item_id, item in old_items.items():
                base = root / "items" / item_id
                for field in ("zh", "en"):
                    path = base / f"{field}.txt"
                    if not path.exists():
                        errors.append(f"{item_id}: 旧数据有、content 缺失")
                        legacy_state = "mismatch"
                        continue
                    if path.read_bytes() != item[field].encode("utf-8"):
                        errors.append(f"{item_id}: {field}.txt 与旧数据不是逐字节一致")
                        legacy_state = "mismatch"
            extra = set(declared) - set(old_items)
            if extra:
                legacy_state = "mismatch"
                errors.append("旧数据没有这些条目：" + ", ".join(sorted(extra)))

    return {
        "ok": not errors,
        "count": len(rebuilt),
        "origins": origins,
        "excerpts": excerpts,
        "digest": digest,
        "legacy": legacy_state,
        "errors": errors,
        "content": str(root),
    }
