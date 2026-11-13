"""来源快照 manifest、内容哈希与完整性校验。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class SourceSnapshotError(ValueError):
    pass


def load_manifest(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceSnapshotError(f"来源 manifest 不可读：{path}（{exc}）") from exc
    if not isinstance(payload, dict):
        raise SourceSnapshotError("来源 manifest 顶层必须是对象")
    if payload.get("schema_version") == 1:
        sources = payload.get("sources")
        if not isinstance(sources, dict):
            raise SourceSnapshotError("来源 manifest 缺少 sources 对象")
        return payload
    # 旧索引是 url -> entry 的平铺对象，读取时兼容但不视为完全校验通过。
    return {"schema_version": 0, "sources": payload}


def verify_entry(root: Path, url: str, entry: dict) -> str | None:
    if not isinstance(entry, dict):
        raise SourceSnapshotError(f"{url} 的 manifest 条目必须是对象")
    name = entry.get("file")
    if not name:
        raise SourceSnapshotError(f"{url} 没有来源快照文件")
    path = root / name
    if not path.exists():
        raise SourceSnapshotError(f"{url} 的来源快照缺失：{path}")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    declared = entry.get("sha256")
    if declared and declared != digest:
        raise SourceSnapshotError(f"{url} 的来源快照 sha256 不匹配")
    if entry.get("size") is not None and entry["size"] != len(data):
        raise SourceSnapshotError(f"{url} 的来源快照大小不匹配")
    return digest


def verify_manifest(manifest_path: Path, urls: set[str] | None = None) -> dict:
    manifest = load_manifest(manifest_path)
    root = manifest_path.parent
    sources = manifest["sources"]
    selected = sorted(urls or sources)
    checked: list[str] = []
    errors: list[str] = []
    for url in selected:
        try:
            verify_entry(root, url, sources.get(url) or {})
            checked.append(url)
        except SourceSnapshotError as exc:
            errors.append(str(exc))
    return {
        "ok": not errors and manifest.get("schema_version") == 1,
        "schema_version": manifest.get("schema_version", 0),
        "generated_at": manifest.get("generated_at"),
        "checked": len(checked),
        "errors": errors,
    }


def snapshot_digest(manifest_path: Path, url: str) -> str:
    manifest = load_manifest(manifest_path)
    entry = manifest["sources"].get(url)
    if not isinstance(entry, dict):
        raise SourceSnapshotError(f"来源未登记：{url}")
    digest = verify_entry(manifest_path.parent, url, entry)
    assert digest is not None
    return digest


__all__ = [
    "SourceSnapshotError",
    "load_manifest",
    "snapshot_digest",
    "verify_entry",
    "verify_manifest",
]
