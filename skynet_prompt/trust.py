"""发布者公钥信任库。"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .signing import SignatureError, verify_manifest_signature


class TrustError(ValueError):
    pass


def load_trust(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrustError(f"信任库不可读：{path}（{exc}）") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("keys"), list):
        raise TrustError("信任库必须是 schema 1 且包含 keys 数组")
    return payload


def save_trust(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def public_key_fingerprint(path: Path) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        der = Path(tmp) / "public.der"
        proc = subprocess.run(
            [
                "openssl", "pkey", "-pubin", "-in", str(path),
                "-outform", "DER", "-out", str(der),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise TrustError("公钥无法解析：" + (proc.stderr or proc.stdout).strip())
        return hashlib.sha256(der.read_bytes()).hexdigest()


def verify_trusted_manifest(manifest: dict, trust_path: Path) -> dict:
    try:
        signature = verify_manifest_signature(manifest)
    except SignatureError as exc:
        raise TrustError(str(exc)) from exc
    trust = load_trust(trust_path)
    key = next(
        (row for row in trust["keys"] if row.get("key_id") == signature["key_id"]),
        None,
    )
    if not key:
        raise TrustError(f"未知签名 key_id：{signature['key_id']}")
    if key.get("status") not in {"dev", "active"}:
        raise TrustError(f"签名 key 不可用：{signature['key_id']}")
    if key.get("expires_at"):
        try:
            expires = datetime.fromisoformat(key["expires_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise TrustError("信任 key expires_at 无效") from exc
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            raise TrustError(f"签名 key 已过期：{signature['key_id']}")
    if key.get("algorithm") != "ed25519":
        raise TrustError("信任 key 算法不是 Ed25519")
    path = trust_path.parent / key["public_key"]
    if not path.exists():
        raise TrustError(f"信任公钥缺失：{path}")
    if public_key_fingerprint(path) != key.get("fingerprint_sha256"):
        raise TrustError("信任公钥指纹不匹配")
    if path.read_text(encoding="utf-8").strip() != signature["public_key_pem"].strip():
        raise TrustError("Pack 内公钥与信任库不一致")
    return signature


def add_key(
    trust_path: Path,
    public_key: Path,
    *,
    key_id: str,
    publisher: str,
    status: str = "active",
    expires_at: str | None = None,
) -> dict:
    if status not in {"active", "dev", "revoked"}:
        raise TrustError(f"未知 key 状态：{status}")
    if not key_id or not publisher:
        raise TrustError("key_id 和 publisher 不能为空")
    payload = load_trust(trust_path)
    if any(row.get("key_id") == key_id for row in payload["keys"]):
        raise TrustError(f"key_id 已存在：{key_id}")
    fingerprint = public_key_fingerprint(public_key)
    row = {
        "key_id": key_id,
        "algorithm": "ed25519",
        "publisher": publisher,
        "public_key": public_key.name,
        "fingerprint_sha256": fingerprint,
        "status": status,
    }
    if expires_at:
        row["expires_at"] = expires_at
    payload["keys"].append(row)
    save_trust(trust_path, payload)
    return row


def revoke_key(trust_path: Path, key_id: str) -> dict:
    payload = load_trust(trust_path)
    row = next((entry for entry in payload["keys"] if entry.get("key_id") == key_id), None)
    if row is None:
        raise TrustError(f"未知 key_id：{key_id}")
    row["status"] = "revoked"
    save_trust(trust_path, payload)
    return row


__all__ = [
    "TrustError",
    "add_key",
    "load_trust",
    "public_key_fingerprint",
    "revoke_key",
    "save_trust",
    "verify_trusted_manifest",
]
