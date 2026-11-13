#!/usr/bin/env python3
"""构建可重复的 Agent 安装 release bundle。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tarfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt import __version__  # noqa: E402
from skynet_prompt.signing import SignatureError, sign_manifest  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tracked_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise SystemExit("build-agent-release: git ls-files 失败")
    paths = [Path(item) for item in completed.stdout.decode().split("\0") if item]
    return [path for path in paths if (ROOT / path).is_file()]


def build_archive(tag: str) -> tuple[bytes, list[dict]]:
    raw = BytesIO()
    entries = []
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for relative in sorted(tracked_files()):
                source = ROOT / relative
                data = source.read_bytes()
                info = tarfile.TarInfo(f"skynet-prompt-{tag}/{relative.as_posix()}")
                info.size = len(data)
                info.mtime = 0
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.mode = 0o755 if source.stat().st_mode & 0o111 else 0o644
                archive.addfile(info, BytesIO(data))
                entries.append({
                    "path": relative.as_posix(),
                    "bytes": len(data),
                    "sha256": sha256(data),
                })
    return raw.getvalue(), entries


def build(
    *,
    tag: str,
    out: Path,
    private_key: Path | None = None,
    key_id: str | None = None,
) -> dict:
    if not tag.startswith("v") or any(char.isspace() for char in tag):
        raise SystemExit("build-agent-release: tag 必须是无空白的 vX.Y.Z")
    if bool(private_key) != bool(key_id):
        raise SystemExit("build-agent-release: --private-key 和 --key-id 必须同时提供")
    archive_data, entries = build_archive(tag)
    archive_name = f"skynet-prompt-{tag}.tar.gz"

    manifest = json.loads((ROOT / "install-manifest.json").read_text(encoding="utf-8"))
    manifest["source"] = {
        "type": "release-archive",
        "tag": tag,
        "archive": archive_name,
        "sha256": sha256(archive_data),
    }
    install_data = (ROOT / "AGENT_INSTALL.md").read_bytes()
    manifest["contract"] = {
        "path": "AGENT_INSTALL.md",
        "sha256": sha256(install_data),
    }
    if private_key is not None:
        try:
            manifest = sign_manifest(manifest, private_key, key_id=key_id or "")
        except SignatureError as exc:
            raise SystemExit(f"build-agent-release: {exc}") from exc
    manifest_data = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    out.mkdir(parents=True, exist_ok=True)
    (out / archive_name).write_bytes(archive_data)
    (out / "install-manifest.json").write_bytes(manifest_data)
    (out / "AGENT_INSTALL.md").write_bytes(install_data)

    files = {
        archive_name: sha256(archive_data),
        "install-manifest.json": sha256(manifest_data),
        "AGENT_INSTALL.md": sha256(install_data),
    }
    checksums = "".join(f"{digest}  {name}\n" for name, digest in files.items())
    (out / "SHA256SUMS").write_text(checksums, encoding="utf-8")

    report = {
        "schema_version": 1,
        "product": manifest["product"],
        "version": manifest["version"],
        "tag": tag,
        "root": f"skynet-prompt-{tag}",
        "files": [
            {"name": name, "bytes": (out / name).stat().st_size, "sha256": digest}
            for name, digest in files.items()
        ],
        "entries": len(entries),
        "entries_sha256": sha256(
            json.dumps(entries, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ),
        "signed": bool(manifest.get("signature")),
        "key_id": (manifest.get("signature") or {}).get("key_id"),
    }
    (out / "release-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建 Agent 安装 release bundle")
    parser.add_argument("--tag", default=f"v{__version__}")
    parser.add_argument("--private-key", type=Path)
    parser.add_argument("--key-id")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "dist" / "agent-release" / f"v{__version__}",
    )
    args = parser.parse_args(argv)
    try:
        report = build(
            tag=args.tag,
            out=args.out,
            private_key=args.private_key,
            key_id=args.key_id,
        )
    except (OSError, SystemExit) as exc:
        print(f"build-agent-release: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
