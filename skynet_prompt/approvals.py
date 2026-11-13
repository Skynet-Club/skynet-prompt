"""团队发布审批：签名记录绑定到 Pack 摘要。"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .signing import SignatureError, sign_manifest
from .trust import TrustError, verify_trusted_manifest

APPROVAL_ROLES = {"reviewer", "publisher"}


class ApprovalError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def create_approval(
    release_dir: Path,
    *,
    approver: str,
    role: str,
    private_key: Path,
    key_id: str,
) -> dict:
    if role not in APPROVAL_ROLES:
        raise ApprovalError(f"审批角色必须是 {sorted(APPROVAL_ROLES)}")
    manifest_path = release_dir / "pack.json"
    prompts_path = release_dir / "prompts.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ApprovalError(f"发布包不可读：{exc}") from exc
    pack_sha = hashlib.sha256(prompts_path.read_bytes()).hexdigest()
    if manifest.get("sha256") != pack_sha or manifest.get("digest") != pack_sha:
        raise ApprovalError("发布包 digest 不一致")
    at = now()
    seed = "\n".join((
        manifest["id"], manifest["version"], manifest["digest"], approver, role, at,
    )).encode("utf-8")
    approval = {
        "schema_version": 1,
        "type": "publish",
        "approval_id": "approval-" + hashlib.sha256(seed).hexdigest()[:12],
        "pack_id": manifest["id"],
        "version": manifest["version"],
        "pack_sha256": manifest["digest"],
        "item_count": len(
            json.loads(prompts_path.read_text(encoding="utf-8"))["items"]
        ),
        "approver": approver,
        "role": role,
        "approved_at": at,
    }
    try:
        return sign_manifest(approval, private_key, key_id=key_id)
    except SignatureError as exc:
        raise ApprovalError(str(exc)) from exc


def verify_approval(path: Path, trust_path: Path, expected: dict) -> dict:
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
        verify_trusted_manifest(approval, trust_path)
    except (OSError, json.JSONDecodeError, TrustError) as exc:
        raise ApprovalError(f"审批签名无效：{path}（{exc}）") from exc
    if approval.get("type") != "publish":
        raise ApprovalError("审批类型必须是 publish")
    if approval.get("role") not in APPROVAL_ROLES:
        raise ApprovalError(f"审批角色无效：{approval.get('role')}")
    for key in ("pack_id", "version", "pack_sha256", "item_count"):
        if approval.get(key) != expected.get(key):
            raise ApprovalError(f"审批与发布包不一致：{key}")
    return approval


def verify_approval_set(
    paths: list[Path],
    trust_path: Path,
    expected: dict,
) -> dict:
    approvals = [verify_approval(path, trust_path, expected) for path in paths]
    roles = {row["role"] for row in approvals}
    missing = APPROVAL_ROLES - roles
    if missing:
        raise ApprovalError("缺少审批角色：" + ", ".join(sorted(missing)))
    by_role = {
        role: next(row for row in approvals if row["role"] == role)
        for role in APPROVAL_ROLES
    }
    if by_role["reviewer"]["approver"] == by_role["publisher"]["approver"]:
        raise ApprovalError("reviewer 与 publisher 必须是不同审批人")
    if (
        by_role["reviewer"]["signature"]["key_id"]
        == by_role["publisher"]["signature"]["key_id"]
    ):
        raise ApprovalError("reviewer 与 publisher 必须使用不同签名 key")
    return {
        "ok": True,
        "count": len(approvals),
        "reviewer": by_role["reviewer"]["approver"],
        "publisher": by_role["publisher"]["approver"],
        "pack_sha256": expected["pack_sha256"],
    }


__all__ = [
    "APPROVAL_ROLES",
    "ApprovalError",
    "create_approval",
    "verify_approval",
    "verify_approval_set",
]
