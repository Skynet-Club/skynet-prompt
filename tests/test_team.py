"""团队 Registry 配置和本地角色授权测试。"""

from __future__ import annotations

import json
from pathlib import Path

from skynet_prompt.team import TeamError, authorize, load_config, resolve_registry, roles_for


def _config(tmp: Path) -> Path:
    path = tmp / "team.json"
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "org_id": "test-org",
            "registries": [{
                "id": "team",
                "source": "/tmp/team/registry.json",
                "channel": "canary",
                "trust": "/tmp/team/keys.json",
                "priority": 10,
            }],
            "members": [
                {"id": "admin", "roles": ["admin", "publisher", "reviewer", "author"]},
                {"id": "reader", "roles": ["reader"]},
            ],
        }),
        encoding="utf-8",
    )
    return path


def test_team_registry_resolves(tmp: Path):
    config = load_config(_config(tmp))
    assert resolve_registry(config, "team")["channel"] == "canary"
    assert roles_for(config, "admin") == {"admin", "publisher", "reviewer", "author"}


def test_roles_authorize_actions(tmp: Path):
    config = load_config(_config(tmp))
    assert authorize(config, "admin", "publish")["ok"] is True
    try:
        authorize(config, "reader", "publish")
    except TeamError as exc:
        assert "无权限" in str(exc)
    else:
        raise AssertionError("reader 不应有发布权限")


def test_duplicate_registry_id_is_rejected(tmp: Path):
    path = _config(tmp)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["registries"].append(dict(data["registries"][0]))
    path.write_text(json.dumps(data), encoding="utf-8")
    try:
        load_config(path)
    except TeamError as exc:
        assert "Registry id 重复" in str(exc)
    else:
        raise AssertionError("重复 Registry 应失败")
