"""本地 HTTP API 黑盒契约。"""

from __future__ import annotations

from skynet_prompt.http_server import make_server, route_get, route_post, static_asset
from skynet_prompt.service import PromptService, PromptServiceError


def test_http_contract():
    service = PromptService()
    status, health = route_get("/v1/health", service)
    assert status == 200 and health["read_only"] is True

    status, capabilities = route_get("/v1/capabilities", service)
    assert status == 200
    assert any(row["id"] == "hermes" for row in capabilities["surfaces"])

    status, packs = route_get("/v1/packs", service)
    assert status == 200 and packs[0]["id"] == "builtin"

    status, categories = route_get("/v1/categories", service)
    assert status == 200 and len(categories) == 9

    status, rows = route_post("/v1/search", {"category": "定验收", "limit": 2}, service)
    assert status == 200 and len(rows) == 2

    status, item = route_get("/v1/items/" + rows[0]["id"], service)
    assert status == 200 and item["id"] == rows[0]["id"]

    ids = [row["id"] for row in rows]
    status, composed = route_post("/v1/compose", {"ids": ids}, service)
    assert status == 200
    assert composed["text"] == "\n\n".join(row["zh"] for row in rows)

    status, error = route_get("/v1/items/missing", service)
    assert status == 404 and "missing" in error["error"]

    status, error = route_post("/v1/search", {"query": 42}, service)
    assert status == 400 and "query" in error["error"]

    content_type, body = static_asset("/")
    assert content_type.startswith("text/html")
    assert b"skynet-prompt" in body
    assert static_asset("/../README.md") is None


def test_http_rejects_non_loopback_bind():
    try:
        make_server(host="0.0.0.0", port=0)
    except PromptServiceError as exc:
        assert "回环" in str(exc)
    else:
        raise AssertionError("非回环地址应该被拒绝")
