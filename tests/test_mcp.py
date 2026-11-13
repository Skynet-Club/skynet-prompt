"""MCP stdio 黑盒契约。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCP = ROOT / "psup-mcp"


def exchange(*requests: dict) -> list[dict]:
    proc = subprocess.run(
        [sys.executable, str(MCP)],
        input="\n".join(json.dumps(request, ensure_ascii=False) for request in requests) + "\n",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def call(request_id: int, name: str, arguments: dict) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }


def test_initialize_and_tool_listing():
    responses = exchange(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )
    assert responses[0]["result"]["serverInfo"]["name"] == "skynet-prompt"
    instructions = responses[0]["result"]["instructions"]
    assert "；；" in instructions
    assert "prompt_search" in instructions
    names = [tool["name"] for tool in responses[1]["result"]["tools"]]
    assert names == ["prompt_packs", "prompt_search", "prompt_get", "prompt_compose"]


def test_search_get_and_compose():
    search = call(1, "prompt_search", {"category": "定验收", "limit": 2})
    responses = exchange(search)
    payload = json.loads(responses[0]["result"]["content"][0]["text"])
    assert len(payload) == 2
    ids = [item["id"] for item in payload]

    get = call(2, "prompt_get", {"id": ids[0]})
    compose = call(3, "prompt_compose", {"ids": ids})
    responses = exchange(get, compose)
    item = json.loads(responses[0]["result"]["content"][0]["text"])
    composed = json.loads(responses[1]["result"]["content"][0]["text"])
    assert item["id"] == ids[0]
    assert composed["text"] == "\n\n".join(entry["zh"] for entry in payload)


def test_tool_errors_are_structured():
    responses = exchange(call(1, "prompt_get", {"id": "missing"}))
    assert responses[0]["result"]["isError"] is True
    payload = json.loads(responses[0]["result"]["content"][0]["text"])
    assert "missing" in payload["error"]


def test_mcp_matches_cli_contract():
    cli_packs = subprocess.run(
        [sys.executable, str(ROOT / "psup"), "packs", "--json"],
        capture_output=True,
        text=True,
    )
    assert cli_packs.returncode == 0, cli_packs.stderr
    mcp_packs = exchange(call(1, "prompt_packs", {}))
    assert json.loads(mcp_packs[0]["result"]["content"][0]["text"]) == json.loads(
        cli_packs.stdout
    )

    cli_items = subprocess.run(
        [
            sys.executable,
            str(ROOT / "psup"),
            "list",
            "--json",
            "--category",
            "定验收",
            "--limit",
            "2",
        ],
        capture_output=True,
        text=True,
    )
    assert cli_items.returncode == 0, cli_items.stderr
    mcp_items = exchange(call(1, "prompt_search", {"category": "定验收", "limit": 2}))
    assert json.loads(mcp_items[0]["result"]["content"][0]["text"]) == json.loads(
        cli_items.stdout
    )
