"""Local-only prompt library admin server.

Run with ``psup admin``. It binds to loopback, serves the small static UI in
``admin_ui/`` and writes through the same JSON/meta contract as ``psup``.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .catalog import (
    CATS,
    CATS_EN,
    DISPLAY,
    DISTRIBUTION,
    EVIDENCE_VERDICTS,
    RIGHTS_BASES,
    PromptCatalog,
    PromptDataError,
    data_dir,
)

UI_DIR = Path(__file__).with_name("admin_ui")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,80}$")
NATURES = ("本人原文", "项目原文", "他人整理", "未核实")


class AdminError(RuntimeError):
    """A validation or persistence error safe to show in the browser."""


def _today() -> str:
    return datetime.now().date().isoformat()


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


class AdminStore:
    """Thread-safe JSON store with atomic writes and timestamped backups."""

    def __init__(self, root: Path | None = None) -> None:
        self.dir = Path(root).expanduser() if root else data_dir()
        self.path = self.dir / "prompts.json"
        self.meta_path = self.dir / "meta.json"
        self.backup_root = self.dir / ".backups"
        self.lock = threading.RLock()

    # -- read ---------------------------------------------------------
    def _read(self) -> tuple[dict, dict]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise AdminError(f"数据不可读：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise AdminError(f"JSON 解析失败：{exc}") from exc
        if not isinstance(data.get("items"), list) or not isinstance(meta, dict):
            raise AdminError("数据结构不正确")
        return data, meta

    def _state(self, data: dict, meta: dict) -> dict:
        body = self.path.read_bytes()
        counts = {key: 0 for _, key in CATS}
        for item in data["items"]:
            counts[item["cat"]] += 1
        categories = [
            {"key": key, "name": name, "en": CATS_EN[key], "count": counts[key]}
            for name, key in CATS
        ]
        return {
            "items": data["items"],
            "categories": categories,
            "meta": meta,
            "sha256": _sha256(body),
            "stats": {
                "count": len(data["items"]),
                "scenes": len(categories),
                "official": sum(
                    1 for item in data["items"]
                    if (item.get("evidence") or {}).get("verdict") == "verbatim"
                ),
            },
        }

    def state(self) -> dict:
        with self.lock:
            data, meta = self._read()
            return self._state(data, meta)

    def export(self) -> dict:
        with self.lock:
            data, _meta = self._read()
            return data

    # -- validate / normalize ----------------------------------------
    def _normalize(self, payload: dict, old: dict | None = None) -> dict:
        if not isinstance(payload, dict):
            raise AdminError("条目必须是 JSON 对象")
        item = copy.deepcopy(old) if old else {}

        def text(field: str, required: bool = True) -> str:
            value = payload.get(field, item.get(field, ""))
            if not isinstance(value, str):
                raise AdminError(f"{field} 必须是字符串")
            value = value.strip()
            if required and not value:
                raise AdminError(f"{field} 不能为空")
            return value

        item["id"] = text("id")
        if not ID_RE.fullmatch(item["id"]):
            raise AdminError("id 只能使用字母、数字、下划线和连字符")
        item["cat"] = text("cat")
        if item["cat"] not in DISPLAY:
            raise AdminError(f"场景不存在：{item['cat']}")
        for field in ("author", "date", "url", "zh", "en"):
            item[field] = text(field)
        item["excerpt"] = bool(payload.get("excerpt", item.get("excerpt", False)))

        nature = payload.get("nature", item.get("nature", "未核实"))
        if nature not in NATURES:
            raise AdminError(f"性质不存在：{nature}")
        item["nature"] = nature

        evidence = dict(item.get("evidence") or {})
        evidence.update(payload.get("evidence") or {})
        verdict = evidence.get("verdict", "unverified")
        if verdict not in EVIDENCE_VERDICTS:
            raise AdminError(f"证据等级不存在：{verdict}")
        evidence["verdict"] = verdict
        evidence.setdefault("checked_at", datetime.now().astimezone().isoformat(timespec="seconds"))
        evidence.setdefault("method", "admin-edit")
        item["evidence"] = evidence

        source = dict(item.get("source") or {})
        source.update(payload.get("source") or {})
        source["url"] = item["url"]
        source["author"] = item["author"]
        source.setdefault("published_at", item["date"])
        source.setdefault("quote", item["en"][:500] + ("…" if len(item["en"]) > 500 else ""))
        license_name = str(source.get("license") or "not-declared").strip()
        rights_basis = source.get("rights_basis", "short-quotation-with-attribution")
        redistribution = source.get("redistribution", "excerpt-only")
        if rights_basis not in RIGHTS_BASES:
            raise AdminError(f"权利依据不存在：{rights_basis}")
        if redistribution not in DISTRIBUTION:
            raise AdminError(f"再分发范围不存在：{redistribution}")
        source["license"] = license_name
        source["rights_basis"] = rights_basis
        source["redistribution"] = redistribution
        if source.get("note") is not None:
            source["note"] = str(source["note"]).strip()
        item["source"] = source
        return item

    def _check_unique(self, data: dict, item: dict, old_id: str | None = None) -> None:
        for row in data["items"]:
            if row["id"] == old_id:
                continue
            if row["id"] == item["id"]:
                raise AdminError(f"id 已存在：{item['id']}")

    # -- write --------------------------------------------------------
    def _write(self, data: dict, meta: dict, label: str) -> dict:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.backup_root / f"{stamp}-{label}"
        backup.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            shutil.copy2(self.path, backup / "prompts.json")
        if self.meta_path.exists():
            shutil.copy2(self.meta_path, backup / "meta.json")

        data = copy.deepcopy(data)
        data["version"] = _today()
        data["count"] = len(data["items"])
        body = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
        meta = copy.deepcopy(meta)
        meta["version"] = _today()
        meta["count"] = data["count"]
        meta["sha256"] = _sha256(body)
        meta["official_count"] = sum(
            1 for item in data["items"]
            if (item.get("evidence") or {}).get("verdict") == "verbatim"
        )
        counts = {key: 0 for _, key in CATS}
        for item in data["items"]:
            counts[item["cat"]] += 1
        meta["cats"] = {
            key: {
                "name": name,
                "en": CATS_EN[key],
                "count": counts[key],
            }
            for name, key in CATS
        }
        meta["evidence"] = {
            verdict: sum(
                1 for item in data["items"]
                if (item.get("evidence") or {}).get("verdict") == verdict
            )
            for verdict in sorted(EVIDENCE_VERDICTS)
        }
        meta["rights"] = {
            basis: sum(
                1 for item in data["items"]
                if (item.get("source") or {}).get("rights_basis") == basis
            )
            for basis in sorted(RIGHTS_BASES)
        }
        natures: dict[str, int] = {}
        for item in data["items"]:
            name = item.get("nature", "未标注")
            natures[name] = natures.get(name, 0) + 1
        meta["natures"] = natures
        meta_body = (json.dumps(meta, ensure_ascii=False, indent=2) + "\n").encode()

        tmp_data = self.path.with_suffix(".json.tmp")
        tmp_meta = self.meta_path.with_suffix(".json.tmp")
        try:
            tmp_data.write_bytes(body)
            tmp_meta.write_bytes(meta_body)
            os.replace(tmp_data, self.path)
            os.replace(tmp_meta, self.meta_path)
            PromptCatalog(self.dir).load()
        except Exception:
            if (backup / "prompts.json").exists():
                shutil.copy2(backup / "prompts.json", self.path)
            if (backup / "meta.json").exists():
                shutil.copy2(backup / "meta.json", self.meta_path)
            raise
        finally:
            tmp_data.unlink(missing_ok=True)
            tmp_meta.unlink(missing_ok=True)
        return {
            "state": self._state(data, meta),
            "backup": str(backup.relative_to(self.dir)),
        }

    def save_item(self, item_id: str | None, payload: dict) -> dict:
        with self.lock:
            data, meta = self._read()
            old = None
            old_id = None
            if item_id is not None:
                for row in data["items"]:
                    if row["id"] == item_id:
                        old = row
                        old_id = row["id"]
                        break
                if old is None:
                    raise AdminError(f"没有 id={item_id}")
            item = self._normalize(payload, old)
            self._check_unique(data, item, old_id)
            if old is None:
                data["items"].append(item)
                label = "create-" + item["id"]
            else:
                old_index = data["items"].index(old)
                data["items"][old_index] = item
                label = "update-" + item["id"]
            result = self._write(data, meta, label)
            result["item"] = item
            return result

    def delete_item(self, item_id: str) -> dict:
        with self.lock:
            data, meta = self._read()
            row = next((row for row in data["items"] if row["id"] == item_id), None)
            if row is None:
                raise AdminError(f"没有 id={item_id}")
            data["items"] = [item for item in data["items"] if item["id"] != item_id]
            return self._write(data, meta, "delete-" + item_id)


class AdminHandler(BaseHTTPRequestHandler):
    server_version = "skynet-prompt-admin"

    def log_message(self, fmt: str, *args: object) -> None:
        if self.path.startswith("/api/"):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self._send(status, body, "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        port = self.server.server_port
        return origin in (f"http://127.0.0.1:{port}", f"http://localhost:{port}")

    def _payload(self) -> dict:
        if not self._origin_ok():
            raise AdminError("拒绝非本机来源的写请求")
        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise AdminError("请求必须是 application/json")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 8 * 1024 * 1024:
            raise AdminError("请求体为空或过大")
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise AdminError(f"JSON 解析失败：{exc}") from exc
        if not isinstance(payload, dict):
            raise AdminError("请求体必须是 JSON 对象")
        return payload

    def _path(self) -> str:
        return unquote(urlparse(self.path).path)

    def do_GET(self) -> None:
        path = self._path()
        try:
            if path == "/api/state":
                self._json(200, self.server.store.state())
                return
            if path == "/api/export":
                body = json.dumps(self.server.store.export(), ensure_ascii=False, indent=2).encode()
                self._send(
                    200, body, "application/json; charset=utf-8",
                    {"Content-Disposition": 'attachment; filename="prompts.json"'},
                )
                return
            if path == "/api/health":
                self._json(200, {"ok": True})
                return
            if path == "/":
                path = "/index.html"
            target = (UI_DIR / path.lstrip("/")).resolve()
            if UI_DIR.resolve() not in target.parents or not target.is_file():
                self._error(404, "not found")
                return
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".svg": "image/svg+xml",
            }.get(target.suffix, "application/octet-stream")
            self._send(200, target.read_bytes(), content_type)
        except (BrokenPipeError, ConnectionResetError):
            return
        except AdminError as exc:
            self._error(400, str(exc))
        except Exception as exc:
            self._error(500, str(exc))

    def do_POST(self) -> None:
        path = self._path()
        try:
            if path != "/api/items":
                self._error(404, "not found")
                return
            result = self.server.store.save_item(None, self._payload())
            self._json(201, result)
        except AdminError as exc:
            self._error(400, str(exc))
        except Exception as exc:
            self._error(500, str(exc))

    def do_PUT(self) -> None:
        path = self._path()
        try:
            prefix = "/api/items/"
            if not path.startswith(prefix):
                self._error(404, "not found")
                return
            item_id = unquote(path[len(prefix):])
            result = self.server.store.save_item(item_id, self._payload())
            self._json(200, result)
        except AdminError as exc:
            self._error(400, str(exc))
        except Exception as exc:
            self._error(500, str(exc))

    def do_DELETE(self) -> None:
        path = self._path()
        try:
            prefix = "/api/items/"
            if not path.startswith(prefix):
                self._error(404, "not found")
                return
            item_id = unquote(path[len(prefix):])
            result = self.server.store.delete_item(item_id)
            self._json(200, result)
        except AdminError as exc:
            self._error(400, str(exc))
        except Exception as exc:
            self._error(500, str(exc))


def run_admin(host: str = "127.0.0.1", port: int = 8788, open_browser: bool = True) -> None:
    if host not in ("127.0.0.1", "localhost"):
        raise AdminError("管理后台只允许绑定 127.0.0.1 或 localhost")
    store = AdminStore()
    store.state()  # fail before binding if the library is broken
    server = ThreadingHTTPServer((host, port), AdminHandler)
    server.store = store  # type: ignore[attr-defined]
    url = f"http://{host}:{port}/"
    print(f"skynet-prompt admin: {url}")
    print(f"data: {store.dir}")
    print("Ctrl-C 停止")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    try:
        run_admin()
    except (AdminError, OSError, PromptDataError) as exc:
        print(f"admin: {exc}", file=sys.stderr)
        raise SystemExit(1)
