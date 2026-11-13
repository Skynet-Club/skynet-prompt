"""Registry 到本地的增量同步、缓存、回滚与诊断测试。"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from skynet_prompt.cas import stats
from skynet_prompt.registry import build_registry
from skynet_prompt.release import release
from skynet_prompt.signing import sign_manifest
from skynet_prompt.sync import doctor, events, pin, rollback, unpin, update
from skynet_prompt.trust import public_key_fingerprint

ROOT = Path(__file__).resolve().parent.parent


def _fixture(tmp: Path) -> tuple[Path, Path, Path]:
    key = tmp / "ed25519.pem"
    proc = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
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
    return key, trust, public


def _second_version(release_dir: Path, key: Path) -> Path:
    second = release_dir.parent / "release-v2"
    shutil.copytree(release_dir, second)
    manifest_path = second / "pack.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = "2026-11-14"
    manifest["published_at"] = "2026-11-14T00:00:00+08:00"
    manifest["signature"] = None
    manifest = sign_manifest(manifest, key, key_id="test-key")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return second


def test_incremental_update_cache_rollback_and_doctor(tmp: Path):
    key, trust, _public = _fixture(tmp)
    release_v1 = tmp / "release-v1"
    release(ROOT, release_v1, private_key=key, key_id="test-key")

    registry_v1 = tmp / "registry-v1"
    build_registry(
        registry_v1,
        [release_v1],
        registry_id="test",
        trust_path=trust,
    )
    store = tmp / "store"
    first = update(
        str(registry_v1 / "registry.json"),
        pack_id="official",
        channel="dev",
        store=store,
        trust_path=trust,
    )
    assert first["updated"] is True
    assert first["version"] == "2026-11-13"

    pinned = pin(
        pack_id="official",
        channel="dev",
        store=store,
        version="2026-11-13",
    )
    assert pinned["pinned_version"] == "2026-11-13"

    release_v2 = _second_version(release_v1, key)
    registry_v2 = tmp / "registry-v2"
    build_registry(
        registry_v2,
        [release_v2],
        registry_id="test",
        trust_path=trust,
    )
    blocked = update(
        str(registry_v2 / "registry.json"),
        pack_id="official",
        channel="dev",
        store=store,
        trust_path=trust,
    )
    assert blocked["updated"] is False
    assert blocked["reason"] == "pinned"

    unpin(pack_id="official", channel="dev", store=store)
    second = update(
        str(registry_v2 / "registry.json"),
        pack_id="official",
        channel="dev",
        store=store,
        trust_path=trust,
    )
    assert second["updated"] is True
    assert second["version"] == "2026-11-14"
    unchanged = update(
        str(registry_v2 / "registry.json"),
        pack_id="official",
        channel="dev",
        store=store,
        trust_path=trust,
    )
    assert unchanged["updated"] is False
    assert unchanged["reason"] == "up-to-date"

    cached = stats(store / "cache")
    assert cached["ok"]
    assert cached["objects"] >= 1

    rolled = rollback(
        pack_id="official",
        channel="dev",
        store=store,
        trust_path=trust,
    )
    assert rolled["version"] == "2026-11-13"

    checked = doctor(
        store,
        trust_path=trust,
        registry_source=str(registry_v2 / "registry.json"),
    )
    assert checked["ok"], checked["errors"]
    assert {"update", "pin", "unpin", "rollback"} <= {
        row["type"] for row in events(store)
    }
