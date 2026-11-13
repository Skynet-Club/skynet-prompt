"""团队发布审批签名与 stable 门测试。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from skynet_prompt.approvals import (
    ApprovalError,
    create_approval,
    verify_approval_set,
)
from skynet_prompt.release import release
from skynet_prompt.trust import public_key_fingerprint

ROOT = Path(__file__).resolve().parent.parent


def _fixture(tmp: Path) -> tuple[Path, Path, Path]:
    keys = []
    public_rows = []
    for name in ("reviewer", "publisher"):
        key = tmp / f"{name}.pem"
        proc = subprocess.run(
            ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
            capture_output=True,
        )
        assert proc.returncode == 0, proc.stderr
        public = tmp / f"{name}.pub.pem"
        proc = subprocess.run(
            ["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(public)],
            capture_output=True,
        )
        assert proc.returncode == 0, proc.stderr
        keys.append(key)
        public_rows.append({
            "key_id": f"test-{name}",
            "algorithm": "ed25519",
            "publisher": "test",
            "public_key": public.name,
            "fingerprint_sha256": public_key_fingerprint(public),
            "status": "active",
        })
    trust = tmp / "keys.json"
    trust.write_text(
        json.dumps({
            "schema_version": 1,
            "keys": public_rows,
        }),
        encoding="utf-8",
    )
    return keys[0], keys[1], trust


def _paths(tmp: Path, release_dir: Path, reviewer_key: Path, publisher_key: Path) -> list[Path]:
    reviewer = create_approval(
        release_dir,
        approver="reviewer@test",
        role="reviewer",
        private_key=reviewer_key,
        key_id="test-reviewer",
    )
    publisher = create_approval(
        release_dir,
        approver="publisher@test",
        role="publisher",
        private_key=publisher_key,
        key_id="test-publisher",
    )
    out = []
    for row in (reviewer, publisher):
        path = tmp / f"{row['approval_id']}.json"
        path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
        out.append(path)
    return out


def test_two_role_approvals_enable_stable_release(tmp: Path):
    reviewer_key, publisher_key, trust = _fixture(tmp)
    dev = tmp / "dev"
    release(ROOT, dev, private_key=reviewer_key, key_id="test-reviewer", trust_path=trust)
    approvals = _paths(tmp, dev, reviewer_key, publisher_key)
    manifest = json.loads((dev / "pack.json").read_text(encoding="utf-8"))
    expected = {
        "pack_id": "official",
        "version": "2026-11-13",
        "pack_sha256": manifest["digest"],
        "item_count": 34,
    }
    verified = verify_approval_set(approvals, trust, expected)
    assert verified["reviewer"] == "reviewer@test"
    assert verified["publisher"] == "publisher@test"

    stable = tmp / "stable"
    report = release(
        ROOT,
        stable,
        channel="stable",
        private_key=publisher_key,
        key_id="test-publisher",
        approval_paths=approvals,
        trust_path=trust,
    )
    assert report["channel"] == "stable"
    assert report["approvals"]["ok"] is True


def test_same_person_cannot_fill_both_roles(tmp: Path):
    reviewer_key, publisher_key, trust = _fixture(tmp)
    dev = tmp / "dev"
    release(ROOT, dev, private_key=reviewer_key, key_id="test-reviewer", trust_path=trust)
    first = create_approval(
        dev,
        approver="same@test",
        role="reviewer",
        private_key=reviewer_key,
        key_id="test-reviewer",
    )
    second = create_approval(
        dev,
        approver="same@test",
        role="publisher",
        private_key=publisher_key,
        key_id="test-publisher",
    )
    paths = []
    for row in (first, second):
        path = tmp / f"{row['approval_id']}.json"
        path.write_text(json.dumps(row), encoding="utf-8")
        paths.append(path)
    manifest = json.loads((dev / "pack.json").read_text(encoding="utf-8"))
    try:
        verify_approval_set(
            paths,
            trust,
            {
                "pack_id": "official",
                "version": "2026-11-13",
                "pack_sha256": manifest["digest"],
                "item_count": 34,
            },
        )
    except ApprovalError as exc:
        assert "不同审批人" in str(exc)
    else:
        raise AssertionError("同一审批人不能同时完成两个角色")
