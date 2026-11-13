"""Prompt Pack Registry manifest 构建、校验和通道选择。"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .catalog import JsonPackSource, PromptDataError
from .trust import TrustError, verify_trusted_manifest


class RegistryError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_pack(
    root: Path,
    release_dir: Path,
    *,
    registry_id: str,
    trust_path: Path,
) -> dict:
    try:
        pack = JsonPackSource(release_dir).load()
    except PromptDataError as exc:
        raise RegistryError(str(exc)) from exc
    manifest = json.loads((release_dir / "pack.json").read_text(encoding="utf-8"))
    if not manifest.get("signature"):
        raise RegistryError(f"{pack.id}@{pack.version} 尚未签名")
    try:
        verify_trusted_manifest(manifest, trust_path)
    except TrustError as exc:
        raise RegistryError(str(exc)) from exc

    version_dir = root / "packs" / pack.id / pack.version
    version_dir.parent.mkdir(parents=True, exist_ok=True)
    if version_dir.exists():
        existing = version_dir / "prompts.json"
        incoming = release_dir / "prompts.json"
        if not existing.exists() or existing.read_bytes() != incoming.read_bytes():
            raise RegistryError(f"不可变版本冲突：{pack.id}@{pack.version}")
    else:
        shutil.copytree(release_dir, version_dir)

    for name in ("pack.json", "prompts.json"):
        if not (version_dir / name).exists():
            raise RegistryError(f"发布包缺少 {name}：{version_dir}")
    return {
        "id": pack.id,
        "name": pack.name,
        "version": pack.version,
        "channel": manifest["channel"],
        "publisher": manifest["publisher"],
        "path": f"packs/{pack.id}/{pack.version}",
        "manifest_sha256": _sha256(version_dir / "pack.json"),
        "items_sha256": _sha256(version_dir / "prompts.json"),
        "min_client_version": manifest["min_client_version"],
        "published_at": manifest["published_at"],
        "signature_key_id": manifest["signature"]["key_id"],
    }


def build_registry(
    root: Path,
    releases: list[Path],
    *,
    registry_id: str,
    trust_path: Path,
) -> dict:
    entries = [
        add_pack(root, release, registry_id=registry_id, trust_path=trust_path)
        for release in releases
    ]
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        key = (entry["id"], entry["version"], entry["channel"])
        if key in seen:
            raise RegistryError(f"Registry 重复条目：{key}")
        seen.add(key)

    payload = {
        "schema_version": 1,
        "registry_id": registry_id,
        "generated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(
            timespec="seconds"
        ),
        "packs": entries,
        "revoked": [],
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def load_registry(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Registry manifest 不可读：{path}（{exc}）") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise RegistryError("Registry schema_version 必须是 1")
    if not isinstance(payload.get("packs"), list) or not isinstance(payload.get("revoked"), list):
        raise RegistryError("Registry 缺少 packs/revoked 数组")
    seen: set[tuple[str, str, str]] = set()
    for entry in payload["packs"]:
        required = (
            "id", "name", "version", "channel", "publisher", "path",
            "manifest_sha256", "items_sha256", "min_client_version",
            "published_at", "signature_key_id",
        )
        missing = [key for key in required if not entry.get(key)]
        if missing:
            raise RegistryError("Registry Pack 缺少字段：" + ", ".join(missing))
        key = (entry["id"], entry["version"], entry["channel"])
        if key in seen:
            raise RegistryError(f"Registry 重复条目：{key}")
        seen.add(key)
    return payload


def select_pack(registry: dict, pack_id: str, channel: str) -> dict:
    revoked = {
        (row.get("id"), row.get("version"))
        for row in registry["revoked"]
    }
    candidates = [
        entry for entry in registry["packs"]
        if entry["id"] == pack_id
        and entry["channel"] == channel
        and (entry["id"], entry["version"]) not in revoked
    ]
    if not candidates:
        raise RegistryError(f"没有可用包：{pack_id} / {channel}")
    return sorted(candidates, key=lambda row: row["published_at"])[-1]


def verify_registry(root: Path, registry: dict, *, trust_path: Path) -> dict:
    errors = []
    for entry in registry["packs"]:
        base = root / entry["path"]
        for name, declared in (
            ("pack.json", entry["manifest_sha256"]),
            ("prompts.json", entry["items_sha256"]),
        ):
            path = base / name
            if not path.exists():
                errors.append(f"缺少 {path}")
            elif _sha256(path) != declared:
                errors.append(f"{path} SHA-256 不匹配")
        try:
            JsonPackSource(base).load()
            manifest = json.loads((base / "pack.json").read_text(encoding="utf-8"))
            verify_trusted_manifest(manifest, trust_path)
        except PromptDataError as exc:
            errors.append(f"{entry['id']}@{entry['version']} 无法加载：{exc}")
        except (TrustError, json.JSONDecodeError) as exc:
            errors.append(f"{entry['id']}@{entry['version']} 签名无效：{exc}")
    return {
        "ok": not errors,
        "registry_id": registry.get("registry_id"),
        "packs": len(registry["packs"]),
        "errors": errors,
    }


__all__ = [
    "RegistryError",
    "build_registry",
    "load_registry",
    "select_pack",
    "verify_registry",
]
