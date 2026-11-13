"""Pack manifest 的 Ed25519 签名与验证。"""

from __future__ import annotations

import base64
import copy
import json
import subprocess
import tempfile
from pathlib import Path


class SignatureError(ValueError):
    pass


def canonical_payload(manifest: dict) -> bytes:
    payload = copy.deepcopy(manifest)
    payload.pop("signature", None)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sign_manifest(manifest: dict, private_key: Path, *, key_id: str) -> dict:
    if not key_id.strip():
        raise SignatureError("key_id 不能为空")
    if not private_key.is_file():
        raise SignatureError(f"签名私钥不存在：{private_key}")
    payload = canonical_payload(manifest)
    with tempfile.TemporaryDirectory() as tmp:
        payload_path = Path(tmp) / "payload.json"
        signature_path = Path(tmp) / "signature.bin"
        payload_path.write_bytes(payload)
        signed = subprocess.run(
            [
                "openssl", "pkeyutl", "-sign", "-rawin",
                "-inkey", str(private_key),
                "-in", str(payload_path),
                "-out", str(signature_path),
            ],
            capture_output=True,
        )
        signature_bytes = (
            signature_path.read_bytes()
            if signature_path.exists()
            else b""
        )
    if signed.returncode != 0:
        raise SignatureError(
            "Ed25519 签名失败：" + signed.stderr.decode("utf-8", "replace").strip()
        )
    public = subprocess.run(
        ["openssl", "pkey", "-in", str(private_key), "-pubout"],
        capture_output=True,
        text=True,
    )
    if public.returncode != 0:
        raise SignatureError(
            "无法导出公钥：" + (public.stderr or public.stdout).strip()
        )
    out = copy.deepcopy(manifest)
    out["signature"] = {
        "algorithm": "ed25519",
        "key_id": key_id,
        "public_key_pem": public.stdout,
        "value": base64.b64encode(signature_bytes).decode("ascii"),
    }
    return out


def verify_manifest_signature(manifest: dict) -> dict:
    signature = manifest.get("signature")
    if not isinstance(signature, dict):
        raise SignatureError("Pack 尚未签名")
    if signature.get("algorithm") != "ed25519":
        raise SignatureError("只支持 Ed25519 签名")
    for key in ("key_id", "public_key_pem", "value"):
        if not signature.get(key):
            raise SignatureError(f"签名缺少 {key}")
    try:
        signature_bytes = base64.b64decode(signature["value"], validate=True)
    except ValueError as exc:
        raise SignatureError("签名值不是有效 Base64") from exc

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        payload = base / "payload.json"
        public = base / "public.pem"
        sig = base / "signature.bin"
        payload.write_bytes(canonical_payload(manifest))
        public.write_text(signature["public_key_pem"], encoding="utf-8")
        sig.write_bytes(signature_bytes)
        verified = subprocess.run(
            [
                "openssl", "pkeyutl", "-verify", "-pubin",
                "-inkey", str(public), "-rawin",
                "-in", str(payload), "-sigfile", str(sig),
            ],
            capture_output=True,
            text=True,
        )
    if verified.returncode != 0:
        raise SignatureError(
            "签名验证失败：" + (verified.stderr or verified.stdout).strip()
        )
    return signature


__all__ = [
    "SignatureError",
    "canonical_payload",
    "sign_manifest",
    "verify_manifest_signature",
]
