"""团队 Registry 配置与本地角色授权。"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROLES = {"admin", "publisher", "reviewer", "author", "reader"}
ACTIONS = {
    "submit": {"admin", "publisher", "reviewer", "author"},
    "review": {"admin", "publisher", "reviewer"},
    "publish": {"admin", "publisher"},
    "admin": {"admin"},
    "read": ROLES,
}


class TeamError(ValueError):
    pass


def default_config() -> Path:
    return Path.home() / ".config" / "skynet-prompt" / "team.json"


def load_config(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TeamError(f"团队配置不可读：{path}（{exc}）") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise TeamError("团队配置 schema_version 必须是 1")
    if not payload.get("org_id") or not isinstance(payload.get("registries"), list):
        raise TeamError("团队配置缺少 org_id/registries")
    if not isinstance(payload.get("members"), list):
        raise TeamError("团队配置缺少 members 数组")

    registry_ids = set()
    for row in payload["registries"]:
        required = ("id", "source", "channel", "trust", "priority")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise TeamError("Registry 缺少字段：" + ", ".join(missing))
        if row["id"] in registry_ids:
            raise TeamError(f"Registry id 重复：{row['id']}")
        if row["channel"] not in {"dev", "canary", "stable"}:
            raise TeamError(f"Registry 通道无效：{row['channel']}")
        registry_ids.add(row["id"])

    member_ids = set()
    for member in payload["members"]:
        member_id = member.get("id")
        roles = member.get("roles")
        if not member_id or member_id in member_ids:
            raise TeamError("团队成员 id 缺失或重复")
        if not isinstance(roles, list) or not roles or not set(roles) <= ROLES:
            raise TeamError(f"成员 {member_id} 的 roles 无效")
        member_ids.add(member_id)
    return payload


def resolve_registry(config: dict, registry_id: str) -> dict:
    row = next(
        (entry for entry in config["registries"] if entry["id"] == registry_id),
        None,
    )
    if row is None:
        raise TeamError(f"没有 Registry：{registry_id}")
    return row


def roles_for(config: dict, member_id: str) -> set[str]:
    member = next(
        (row for row in config["members"] if row.get("id") == member_id),
        None,
    )
    if member is None:
        raise TeamError(f"未知团队成员：{member_id}")
    return set(member["roles"])


def authorize(config: dict, member_id: str, action: str) -> dict:
    if action not in ACTIONS:
        raise TeamError(f"未知动作：{action}")
    roles = roles_for(config, member_id)
    allowed = bool(roles & ACTIONS[action])
    if not allowed:
        raise TeamError(f"成员 {member_id} 无权限执行 {action}")
    return {
        "ok": True,
        "member": member_id,
        "action": action,
        "roles": sorted(roles),
    }


def config_env() -> Path:
    return Path(
        os.environ.get("SKYNET_PROMPT_TEAM_CONFIG") or default_config()
    ).expanduser()


__all__ = [
    "ACTIONS",
    "ROLES",
    "TeamError",
    "authorize",
    "config_env",
    "default_config",
    "load_config",
    "resolve_registry",
    "roles_for",
]
