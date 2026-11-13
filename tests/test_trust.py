"""第三方发布者信任库管理测试。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from skynet_prompt.signing import sign_manifest
from skynet_prompt.trust import TrustError, add_key, load_trust, revoke_key, verify_trusted_manifest


def _keys(tmp: Path) -> tuple[Path, Path, Path]:
    key = tmp / "publisher.pem"
    public = tmp / "publisher.pub.pem"
    proc = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    proc = subprocess.run(
        ["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(public)],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    trust = tmp / "keys.json"
    trust.write_text('{"schema_version":1,"keys":[]}\n', encoding="utf-8")
    return key, public, trust


def test_add_and_revoke_third_party_key(tmp: Path):
    key, public, trust = _keys(tmp)
    row = add_key(
        trust,
        public,
        key_id="third-party",
        publisher="Third",
    )
    assert len(row["fingerprint_sha256"]) == 64
    manifest = sign_manifest({"version": "1"}, key, key_id="third-party")
    assert verify_trusted_manifest(manifest, trust)["key_id"] == "third-party"

    revoked = revoke_key(trust, "third-party")
    assert revoked["status"] == "revoked"
    try:
        verify_trusted_manifest(manifest, trust)
    except TrustError as exc:
        assert "不可用" in str(exc)
    else:
        raise AssertionError("撤销后的 key 不应通过")


def test_duplicate_key_id_is_rejected(tmp: Path):
    _, public, trust = _keys(tmp)
    add_key(trust, public, key_id="same", publisher="Third")
    try:
        add_key(trust, public, key_id="same", publisher="Third")
    except TrustError as exc:
        assert "已存在" in str(exc)
    else:
        raise AssertionError("重复 key_id 应失败")
