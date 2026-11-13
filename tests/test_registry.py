"""Registry 构建、校验和通道选择测试。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from skynet_prompt.registry import build_registry, load_registry, select_pack, verify_registry
from skynet_prompt.release import release
from skynet_prompt.trust import public_key_fingerprint

ROOT = Path(__file__).resolve().parent.parent


def _key(tmp: Path) -> Path:
    key = tmp / "ed25519.pem"
    proc = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    return key


def test_registry_selects_signed_pack(tmp: Path):
    key = _key(tmp)
    public = tmp / "ed25519.pub.pem"
    proc = subprocess.run(
        ["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(public)],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    trust = tmp / "keys.json"
    trust.write_text(
        json.dumps({
            "schema_version": 1,
            "keys": [{
                "key_id": "test-key",
                "algorithm": "ed25519",
                "publisher": "test",
                "public_key": public.name,
                "fingerprint_sha256": public_key_fingerprint(public),
                "status": "active",
            }],
        }),
        encoding="utf-8",
    )
    release_dir = tmp / "release"
    release(ROOT, release_dir, private_key=key, key_id="test-key")
    registry_root = tmp / "registry"
    built = build_registry(
        registry_root,
        [release_dir],
        registry_id="skynet-test",
        trust_path=trust,
    )
    loaded = load_registry(registry_root / "registry.json")
    assert loaded == built
    assert verify_registry(
        registry_root,
        loaded,
        trust_path=trust,
    )["ok"]
    selected = select_pack(loaded, "official", "dev")
    assert selected["version"] == "2026-11-13"
    assert selected["signature_key_id"] == "test-key"
