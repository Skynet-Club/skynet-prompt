"""本地只读 HTTP API，供 GUI、Web 和第三方客户端使用。"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import __version__
from .compat import capability_manifest
from .service import PromptService, PromptServiceError

MAX_BODY = 1024 * 1024
WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def static_asset(path: str) -> tuple[str, bytes] | None:
    target = STATIC_FILES.get(path)
    if target is None:
        return None
    name, content_type = target
    return content_type, (WEB_ROOT / name).read_bytes()


def _error_payload(message: str) -> dict:
    return {"ok": False, "error": message}


def route_get(path: str, service: PromptService) -> tuple[int, object]:
    if path == "/v1/health":
        return HTTPStatus.OK, {
            "ok": True,
            "name": "skynet-prompt",
            "version": __version__,
            "read_only": True,
        }
    if path == "/v1/capabilities":
        manifest = capability_manifest()
        return HTTPStatus.OK, {
            "ok": True,
            "api_version": "v1",
            "read_only": True,
            "core_capabilities": ["packs", "search", "get", "compose", "audit"],
            **manifest,
        }
    if path == "/v1/packs":
        return HTTPStatus.OK, service.packs()
    if path == "/v1/categories":
        return HTTPStatus.OK, service.categories()
    if path == "/v1/audit":
        return HTTPStatus.OK, service.audit()
    if path.startswith("/v1/items/"):
        item_id = unquote(path.removeprefix("/v1/items/"))
        try:
            return HTTPStatus.OK, service.get(item_id)
        except PromptServiceError as exc:
            return HTTPStatus.NOT_FOUND, _error_payload(str(exc))
    return HTTPStatus.NOT_FOUND, _error_payload("未知路径")


def route_post(path: str, args: dict, service: PromptService) -> tuple[int, object]:
    if path not in {"/v1/search", "/v1/compose"}:
        return HTTPStatus.NOT_FOUND, _error_payload("未知路径")
    try:
        if path == "/v1/search":
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
            if limit is not None and (
                not isinstance(limit, int) or isinstance(limit, bool)
            ):
                raise PromptServiceError("limit 必须是整数")
            return HTTPStatus.OK, service.search(
                query,
                category=category,
                pack=pack,
                limit=limit,
            )

        ids = args.get("ids")
        if not isinstance(ids, list) or not all(isinstance(v, str) for v in ids):
            raise PromptServiceError("ids 必须是字符串数组")
        field = args.get("field", "zh")
        separator = args.get("separator", "\n\n")
        if not isinstance(field, str) or not isinstance(separator, str):
            raise PromptServiceError("field/separator 必须是字符串")
        return HTTPStatus.OK, service.compose(
            ids,
            field=field,
            separator=separator,
        )
    except PromptServiceError as exc:
        return HTTPStatus.BAD_REQUEST, _error_payload(str(exc))


class PromptHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, service: PromptService | None = None):
        self.service = service or PromptService()
        super().__init__(address, PromptRequestHandler)


class PromptRequestHandler(BaseHTTPRequestHandler):
    server: PromptHTTPServer
    server_version = f"skynet-prompt/{__version__}"

    def log_message(self, fmt: str, *args) -> None:
        print(f"psupd: {fmt % args}", file=sys.stderr)

    def _send(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, content_type: str, body: bytes) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._send(status, {"ok": False, "error": message})

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise PromptServiceError("Content-Length 无效") from exc
        if length < 0 or length > MAX_BODY:
            raise PromptServiceError("请求体过大")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError as exc:
            raise PromptServiceError(f"JSON 解析失败：{exc}") from exc
        if not isinstance(payload, dict):
            raise PromptServiceError("请求体必须是对象")
        return payload

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        asset = static_asset(path)
        if asset is not None:
            self._send_static(*asset)
            return
        self._send(*route_get(path, self.server.service))

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            args = self._body()
        except PromptServiceError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send(*route_post(path, args, self.server.service))


def make_server(host: str = "127.0.0.1", port: int = 8765) -> PromptHTTPServer:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise PromptServiceError("只接受 IP 回环地址") from exc
    if not address.is_loopback:
        raise PromptServiceError("只允许绑定回环地址")
    return PromptHTTPServer((host, port))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="psupd")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        server = make_server(args.host, args.port)
    except (OSError, PromptServiceError) as exc:
        print(f"psupd: {exc}", file=sys.stderr)
        return 1
    host, port = server.server_address[:2]
    print(f"psupd listening http://{host}:{port}", file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
