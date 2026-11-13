"""最小只读 MCP stdio server。"""

from __future__ import annotations

import json
import sys
from typing import TextIO

from . import __version__
from .service import PromptService, PromptServiceError
from .trigger import ASCII_TRIGGER, CANONICAL_TRIGGER, LITERAL_ESCAPE

SUPPORTED_PROTOCOLS = {
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
}
DEFAULT_PROTOCOL = "2025-06-18"

TOOLS = [
    {
        "name": "prompt_packs",
        "description": "列出本地已加载的提示词包及版本和 SHA-256。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "prompt_search",
        "description": "按关键词、类目或提示词包搜索条目。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "多个空格分隔的词必须全部命中。"},
                "category": {"type": "string", "description": "类目键或显示名。"},
                "pack": {"type": "string", "description": "提示词包 id。"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "prompt_get",
        "description": "按稳定 id 读取一个提示词条目。",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "prompt_compose",
        "description": "按给定顺序确定性拼接多个提示词，不调用模型。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                "field": {"type": "string", "enum": ["zh", "en"], "default": "zh"},
                "separator": {"type": "string", "default": "\n\n"},
            },
            "required": ["ids"],
            "additionalProperties": False,
        },
    },
]


def _text_result(payload, *, is_error: bool = False) -> dict:
    return {
        "content": [{
            "type": "text",
            "text": json.dumps(payload, ensure_ascii=False),
        }],
        "isError": is_error,
    }


def _call_tool(service: PromptService, name: str, args: dict) -> dict:
    try:
        if name == "prompt_packs":
            return _text_result(service.packs())
        if name == "prompt_search":
            query = args.get("query", "")
            category = args.get("category")
            pack = args.get("pack")
            limit = args.get("limit")
            if not isinstance(query, str):
                raise PromptServiceError("query 必须是字符串")
            if category is not None and not isinstance(category, str):
                raise PromptServiceError("category 必须是字符串")
            if pack is not None and not isinstance(pack, str):
                raise PromptServiceError("pack 必须是字符串")
            if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool)):
                raise PromptServiceError("limit 必须是整数")
            return _text_result(service.search(query, category=category, pack=pack, limit=limit))
        if name == "prompt_get":
            item_id = args.get("id")
            if not isinstance(item_id, str) or not item_id:
                raise PromptServiceError("id 必须是非空字符串")
            return _text_result(service.get(item_id))
        if name == "prompt_compose":
            ids = args.get("ids")
            field = args.get("field", "zh")
            separator = args.get("separator", "\n\n")
            if not isinstance(ids, list) or not all(isinstance(v, str) for v in ids):
                raise PromptServiceError("ids 必须是字符串数组")
            if not isinstance(field, str) or not isinstance(separator, str):
                raise PromptServiceError("field/separator 必须是字符串")
            return _text_result(service.compose(ids, field=field, separator=separator))
        return _text_result({"error": f"未知工具 {name}"}, is_error=True)
    except PromptServiceError as exc:
        return _text_result({"error": str(exc)}, is_error=True)


def handle_request(payload: dict, service: PromptService) -> dict | None:
    method = payload.get("method")
    request_id = payload.get("id")
    params = payload.get("params") or {}

    if request_id is None:
        return None
    if method == "initialize":
        requested = params.get("protocolVersion")
        protocol = requested if requested in SUPPORTED_PROTOCOLS else DEFAULT_PROTOCOL
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "skynet-prompt", "version": __version__},
                "instructions": (
                    f"当用户消息以 {CANONICAL_TRIGGER}（兼容 {ASCII_TRIGGER}）开头时，"
                    "先调用 prompt_search；用户给出 id 后再调用 prompt_get。"
                    "返回正文时必须原样保留，并展示来源、作者、许可和版本。"
                    f"单独输入 {LITERAL_ESCAPE} 表示字面量触发器，不调用工具。"
                ),
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(name, str) or not isinstance(args, dict):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": "tools/call 参数无效"},
            }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": _call_tool(service, name, args),
        }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"未知方法 {method}"},
    }


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    service = PromptService()
    for line in stdin:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"JSON 解析失败：{exc}"},
            }
        else:
            response = handle_request(payload, service) if isinstance(payload, dict) else {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "请求必须是对象"},
            }
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
            stdout.flush()
    return 0


def main() -> int:
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
