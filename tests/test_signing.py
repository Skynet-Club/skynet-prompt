"""Ed25519 manifest 签名测试。"""

from __future__ import annotations

import copy
import subprocess
from pathlib import Path

from skynet_prompt.signing import (
    SignatureError,
    canonical_payload,
    sign_manifest,
    verify_manifest_signature,
)


def _manifest() -> dict:
    return {
        "schema_version": 2,
        "id": "official",
        "version": "1",
        "signature": None,
    }


def _key(tmp: Path) -> Path:
    key = tmp / "ed25519.pem"
    proc = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    return key


def test_sign_and_verify_manifest(tmp: Path):
    manifest = sign_manifest(_manifest(), _key(tmp), key_id="test-key")
    signature = verify_manifest_signature(manifest)
    assert signature["key_id"] == "test-key"
    assert signature["algorithm"] == "ed25519"


def test_changed_manifest_fails_signature(tmp: Path):
    manifest = sign_manifest(_manifest(), _key(tmp), key_id="test-key")
    changed = copy.deepcopy(manifest)
    changed["version"] = "2"
    try:
        verify_manifest_signature(changed)
    except SignatureError as exc:
        assert "签名验证失败" in str(exc)
    else:
        raise AssertionError("篡改 manifest 应导致签名失败")


def test_signature_is_not_part_of_payload():
    first = _manifest()
    second = copy.deepcopy(first)
    second["signature"] = {"value": "ignored"}
    assert canonical_payload(first) == canonical_payload(second)
