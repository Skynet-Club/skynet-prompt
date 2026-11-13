"""Registry → 本地 Pack 的增量安装、绑定、回滚和诊断。"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

from . import __version__
from .cas import materialize, put_file
from .catalog import JsonPackSource, PromptDataError
from .registry import RegistryError, load_registry, select_pack, verify_registry
from .trust import TrustError, verify_trusted_manifest

SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
MAX_FILE = 32 * 1024 * 1024


class SyncError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def default_store() -> Path:
    return Path.home() / ".local" / "share" / "skynet-prompt"


def _state_path(store: Path) -> Path:
    return store / "state.json"


def load_state(store: Path) -> dict:
    path = _state_path(store)
    if not path.exists():
        return {"schema_version": 1, "bindings": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"本地状态损坏：{path}（{exc}）") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("bindings"), dict):
        raise SyncError("本地状态 schema 无效")
    return payload


def save_state(store: Path, state: dict) -> None:
    store.mkdir(parents=True, exist_ok=True)
    target = _state_path(store)
    with tempfile.NamedTemporaryFile(dir=store, delete=False) as handle:
        tmp = Path(handle.name)
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def append_event(store: Path, event: dict) -> None:
    store.mkdir(parents=True, exist_ok=True)
    path = store / "events.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": now(), **event}, ensure_ascii=False) + "\n")


def events(store: Path, limit: int = 100) -> list[dict]:
    path = store / "events.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows[-max(limit, 1):]


def _safe(value: str, label: str) -> str:
    if not SAFE_NAME.fullmatch(value):
        raise SyncError(f"{label} 含非法字符：{value}")
    return value


def _load_registry_source(source: str) -> tuple[dict, str | None, Path | None]:
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        try:
            with urllib.request.urlopen(source, timeout=20) as response:
                data = response.read(MAX_FILE + 1)
        except OSError as exc:
            raise SyncError(f"Registry 下载失败：{exc}") from exc
        if len(data) > MAX_FILE:
            raise SyncError("Registry manifest 超过大小限制")
        return json.loads(data), source, None
    path = Path(source).expanduser()
    return load_registry(path), None, path.parent


def _download(url: str, target: Path) -> None:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read(MAX_FILE + 1)
    except OSError as exc:
        raise SyncError(f"下载失败 {url}：{exc}") from exc
    if len(data) > MAX_FILE:
        raise SyncError(f"文件超过大小限制：{url}")
    target.write_bytes(data)


def _stage_pack(
    store: Path,
    entry: dict,
    *,
    registry_url: str | None,
    local_root: Path | None,
    staging: Path,
) -> None:
    rel = Path(entry["path"])
    if rel.is_absolute() or ".." in rel.parts:
        raise SyncError("Registry Pack 路径非法")
    if local_root is not None:
        source = local_root / rel
        if not source.is_dir():
            raise SyncError(f"Registry Pack 目录缺失：{source}")
        shutil.copytree(source, staging, dirs_exist_ok=True)
        return
    assert registry_url is not None
    base = urljoin(registry_url, rel.as_posix().rstrip("/") + "/")
    staging.mkdir(parents=True, exist_ok=True)
    for name in ("pack.json", "prompts.json", "meta.json", "release-report.json"):
        target = staging / name
        try:
            _download(urljoin(base, name), target)
        except SyncError:
            if name != "release-report.json":
                raise


def _verify_installed(path: Path, trust_path: Path) -> dict:
    try:
        pack = JsonPackSource(path).load()
        manifest = json.loads((path / "pack.json").read_text(encoding="utf-8"))
        verify_trusted_manifest(manifest, trust_path)
    except (PromptDataError, TrustError, OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"本地 Pack 校验失败：{path}（{exc}）") from exc
    return manifest


def update(
    registry_source: str,
    *,
    pack_id: str,
    channel: str,
    store: Path,
    trust_path: Path,
) -> dict:
    _safe(pack_id, "pack_id")
    _safe(channel, "channel")
    registry, registry_url, local_root = _load_registry_source(registry_source)
    try:
        entry = select_pack(registry, pack_id, channel)
    except RegistryError as exc:
        raise SyncError(str(exc)) from exc
    version = _safe(entry["version"], "version")
    state = load_state(store)
    key = f"{pack_id}:{channel}"
    binding = state["bindings"].get(key) or {}
    pinned = binding.get("pinned_version")
    if pinned and pinned != entry["version"]:
        return {
            "ok": True,
            "updated": False,
            "reason": "pinned",
            "pack_id": pack_id,
            "version": binding.get("version"),
            "pinned_version": pinned,
            "available_version": entry["version"],
        }
    if binding.get("version") == version:
        installed = store / binding["path"]
        _verify_installed(installed, trust_path)
        return {
            "ok": True,
            "updated": False,
            "reason": "up-to-date",
            "pack_id": pack_id,
            "version": version,
            "path": str(installed),
        }

    final = store / "packs" / pack_id / version
    if final.exists():
        _verify_installed(final, trust_path)
    else:
        staging_root = store / "staging"
        staging_root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(
            prefix=f"{pack_id}-{version}-",
            dir=staging_root,
        ))
        _stage_pack(
            store,
            entry,
            registry_url=registry_url,
            local_root=local_root,
            staging=staging,
        )
        prompts = staging / "prompts.json"
        if not prompts.exists():
            raise SyncError("Pack 缺少 prompts.json")
        digest = put_file(store / "cache", prompts)
        prompts.unlink()
        materialize(store / "cache", digest, prompts)
        _verify_installed(staging, trust_path)
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, final)

    previous = list(binding.get("previous") or [])
    if binding.get("version") and binding["version"] != version:
        previous.append(binding["version"])
    binding = {
        "pack_id": pack_id,
        "channel": channel,
        "version": version,
        "path": str(final.relative_to(store)),
        "installed_at": now(),
        "min_client_version": entry["min_client_version"],
        "previous": previous[-10:],
    }
    state["bindings"][key] = binding
    save_state(store, state)
    append_event(store, {
        "type": "update",
        "pack_id": pack_id,
        "channel": channel,
        "version": version,
    })
    return {
        "ok": True,
        "updated": True,
        "pack_id": pack_id,
        "version": version,
        "path": str(final),
    }


def rollback(
    *,
    pack_id: str,
    channel: str,
    store: Path,
    trust_path: Path,
) -> dict:
    state = load_state(store)
    key = f"{pack_id}:{channel}"
    binding = state["bindings"].get(key)
    if not binding or not binding.get("previous"):
        raise SyncError(f"没有可回滚版本：{key}")
    previous = list(binding["previous"])
    version = previous.pop()
    target = store / "packs" / pack_id / version
    _verify_installed(target, trust_path)
    binding["previous"] = [*previous, binding["version"]]
    binding["version"] = version
    binding["path"] = str(target.relative_to(store))
    binding["installed_at"] = now()
    state["bindings"][key] = binding
    save_state(store, state)
    append_event(store, {
        "type": "rollback",
        "pack_id": pack_id,
        "channel": channel,
        "version": version,
    })
    return {
        "ok": True,
        "rolled_back": True,
        "pack_id": pack_id,
        "version": version,
        "path": str(target),
    }


def pin(
    *,
    pack_id: str,
    channel: str,
    store: Path,
    version: str | None = None,
) -> dict:
    state = load_state(store)
    key = f"{pack_id}:{channel}"
    binding = state["bindings"].get(key)
    if not binding:
        raise SyncError(f"尚未安装：{key}")
    pinned = version or binding["version"]
    if pinned != binding["version"] and pinned not in binding.get("previous", []):
        raise SyncError(f"只能固定当前或历史已安装版本：{pinned}")
    binding["pinned_version"] = pinned
    save_state(store, state)
    append_event(store, {
        "type": "pin",
        "pack_id": pack_id,
        "channel": channel,
        "version": pinned,
    })
    return {"ok": True, "pack_id": pack_id, "channel": channel, "pinned_version": pinned}


def unpin(*, pack_id: str, channel: str, store: Path) -> dict:
    state = load_state(store)
    key = f"{pack_id}:{channel}"
    binding = state["bindings"].get(key)
    if not binding:
        raise SyncError(f"尚未安装：{key}")
    binding.pop("pinned_version", None)
    save_state(store, state)
    append_event(store, {
        "type": "unpin",
        "pack_id": pack_id,
        "channel": channel,
    })
    return {"ok": True, "pack_id": pack_id, "channel": channel, "pinned": False}


def doctor(
    store: Path,
    *,
    trust_path: Path,
    registry_source: str | None = None,
) -> dict:
    errors = []
    state = load_state(store)
    checked = []
    for key, binding in state["bindings"].items():
        try:
            path = store / binding["path"]
            _verify_installed(path, trust_path)
            if _version_tuple(binding.get("min_client_version", __version__)) > _version_tuple(__version__):
                raise SyncError(f"客户端版本过低：{__version__}")
            checked.append(key)
        except SyncError as exc:
            errors.append(str(exc))
    registry = None
    if registry_source:
        try:
            registry, registry_url, local_root = _load_registry_source(registry_source)
            if local_root is not None:
                result = verify_registry(local_root, registry, trust_path=trust_path)
                errors.extend(result["errors"])
            else:
                for entry in registry["packs"]:
                    _safe(entry["id"], "pack_id")
                    _safe(entry["version"], "version")
                    if urlparse(entry["path"]).scheme or ".." in Path(entry["path"]).parts:
                        errors.append("Registry Pack 路径非法")
        except (SyncError, RegistryError) as exc:
            errors.append(str(exc))
    return {
        "ok": not errors,
        "store": str(store),
        "bindings": checked,
        "registry_packs": len(registry["packs"]) if registry else None,
        "errors": errors,
    }


def _version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError:
        return (0,)


__all__ = [
    "SyncError",
    "default_store",
    "doctor",
    "events",
    "load_state",
    "pin",
    "rollback",
    "save_state",
    "unpin",
    "update",
]
