"""本地内容寻址缓存。"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path


class CacheError(ValueError):
    pass


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def object_path(root: Path, digest: str) -> Path:
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise CacheError("缓存 digest 必须是 64 位小写 SHA-256")
    return root / "objects" / digest[:2] / digest[2:]


def put_bytes(root: Path, data: bytes) -> str:
    digest = digest_bytes(data)
    target = object_path(root, digest)
    if target.exists():
        if digest_file(target) != digest:
            raise CacheError(f"缓存对象损坏：{target}")
        return digest
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        handle.write(data)
        tmp = Path(handle.name)
    os.replace(tmp, target)
    return digest


def put_file(root: Path, source: Path) -> str:
    digest = digest_file(source)
    target = object_path(root, digest)
    if target.exists():
        if digest_file(target) != digest:
            raise CacheError(f"缓存对象损坏：{target}")
        return digest
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        tmp = Path(handle.name)
    shutil.copyfile(source, tmp)
    os.replace(tmp, target)
    return digest


def materialize(root: Path, digest: str, destination: Path) -> None:
    source = object_path(root, digest)
    if not source.exists() or digest_file(source) != digest:
        raise CacheError(f"缓存对象缺失或损坏：{digest}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copyfile(source, destination)


def stats(root: Path) -> dict:
    counts = 0
    size = 0
    corrupt = []
    objects = root / "objects"
    if objects.exists():
        for path in objects.glob("*/*"):
            if not path.is_file():
                continue
            counts += 1
            size += path.stat().st_size
            digest = path.parent.name + path.name
            if digest_file(path) != digest:
                corrupt.append(str(path))
    return {
        "ok": not corrupt,
        "objects": counts,
        "bytes": size,
        "corrupt": corrupt,
    }


__all__ = [
    "CacheError",
    "digest_bytes",
    "digest_file",
    "materialize",
    "object_path",
    "put_bytes",
    "put_file",
    "stats",
]
