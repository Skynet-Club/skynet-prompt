#!/usr/bin/env python3
"""Agent 可调用的确定性安装执行器。

默认只读计划；``--apply`` 才修改用户目录。所有模式输出一个 JSON 对象。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt import __version__  # noqa: E402
from skynet_prompt.signing import SignatureError, verify_manifest_signature  # noqa: E402
from skynet_prompt.trust import TrustError, verify_trusted_manifest  # noqa: E402
from skynet_prompt.trigger import CANONICAL_TRIGGER  # noqa: E402


class ContractError(ValueError):
    pass


def _inside_root(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ContractError(f"路径越界：{relative}") from exc
    if not path.is_file():
        raise ContractError(f"文件不存在：{relative}")
    return path


def load_manifest(path: Path, trust_path: Path | None = None) -> dict:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"无法读取 manifest：{exc}") from exc
    if not isinstance(manifest, dict):
        raise ContractError("manifest 顶层必须是对象")
    required = {
        "schema_version", "product", "version", "trigger", "entrypoint",
        "installer", "platforms", "adapters", "verification", "safety",
        "source",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ContractError(f"manifest 缺少字段：{', '.join(missing)}")
    if manifest["schema_version"] != 1:
        raise ContractError("只支持 manifest schema_version=1")
    if manifest["product"] != "skynet-prompt":
        raise ContractError("manifest product 不匹配")
    if manifest["version"] != __version__:
        raise ContractError(
            f"manifest 版本 {manifest['version']} 与产品版本 {__version__} 不一致"
        )
    if manifest["trigger"] != CANONICAL_TRIGGER:
        raise ContractError(f"manifest trigger 必须是 {CANONICAL_TRIGGER}")
    if not isinstance(manifest["source"], dict):
        raise ContractError("source 必须是对象")
    if manifest.get("signature") is not None:
        try:
            verify_manifest_signature(manifest)
        except SignatureError as exc:
            raise ContractError(f"manifest 签名无效：{exc}") from exc
    if trust_path is not None:
        try:
            verify_trusted_manifest(manifest, trust_path)
        except TrustError as exc:
            raise ContractError(f"manifest 信任校验失败：{exc}") from exc
    if not isinstance(manifest["platforms"], list) or not manifest["platforms"]:
        raise ContractError("platforms 必须是非空数组")
    contract = manifest.get("contract")
    if contract is not None:
        if not isinstance(contract, dict) or not contract.get("path") or not contract.get("sha256"):
            raise ContractError("contract 必须包含 path 和 sha256")
        contract_path = _inside_root(str(contract["path"]))
        actual = hashlib.sha256(contract_path.read_bytes()).hexdigest()
        if actual != contract["sha256"]:
            raise ContractError("AGENT_INSTALL.md 哈希与 manifest 不一致")
    if platform.system().lower() not in manifest["platforms"]:
        raise ContractError(f"不支持当前平台：{platform.system().lower()}")

    _inside_root(str(manifest["entrypoint"]))
    _inside_root(str(manifest["installer"]))
    adapters = manifest["adapters"]
    if not isinstance(adapters, list) or not adapters:
        raise ContractError("manifest adapters 必须是非空数组")
    ids = []
    for adapter in adapters:
        if not isinstance(adapter, dict):
            raise ContractError("adapter 必须是对象")
        adapter_id = adapter.get("id")
        if not isinstance(adapter_id, str) or not adapter_id:
            raise ContractError("adapter.id 必须是非空字符串")
        if not isinstance(adapter.get("install_args"), list):
            raise ContractError(f"{adapter_id}.install_args 必须是数组")
        allowed_args = {"codex", "pi", "opencode", "hermes", "copilot", "claude"}
        if not set(adapter["install_args"]).issubset(allowed_args):
            raise ContractError(f"{adapter_id}.install_args 含未知值")
        ids.append(adapter_id)
    if len(ids) != len(set(ids)):
        raise ContractError("adapter.id 不能重复")
    if "cli" not in ids:
        raise ContractError("manifest 必须包含 cli 降级适配器")
    safety = manifest["safety"]
    if not isinstance(safety, dict):
        raise ContractError("safety 必须是对象")
    if safety.get("requires_sudo") is not False:
        raise ContractError("安装契约不允许 sudo")
    if safety.get("reads_credentials") is not False:
        raise ContractError("安装契约不允许读取凭据")
    if safety.get("sends_prompts") is not False:
        raise ContractError("安装契约不允许发送提示词")
    if safety.get("plan_before_apply") is not True:
        raise ContractError("安装契约必须要求先计划")
    if safety.get("remote_script_execution") is not False:
        raise ContractError("安装契约不允许远程脚本执行")
    if safety.get("immutable_source_required_for_release") is not True:
        raise ContractError("发布安装必须要求不可变来源")
    for case in manifest["verification"]:
        command = case.get("command") if isinstance(case, dict) else None
        if not isinstance(command, list) or not command or command[0] != "psup":
            raise ContractError("verification.command 必须以 psup 开头")
    return manifest


def detect_adapters(manifest: dict) -> list[dict]:
    rows = []
    for adapter in manifest["adapters"]:
        detect = adapter.get("detect") or {}
        command = detect.get("command")
        if detect.get("always") is True:
            path = sys.executable
            available = True
        elif isinstance(command, str):
            path = shutil.which(command)
            available = path is not None
        else:
            path = None
            available = False
        version = None
        compatible = available
        reason = None
        spec = adapter.get("version")
        if available and spec and path:
            try:
                command = [str(path), *spec["command"][1:]]
                checked = subprocess.run(command, capture_output=True, text=True, timeout=15)
                match = re.search(spec["regex"], checked.stdout + checked.stderr)
                version = match.group(1) if match else None
                if version is None:
                    compatible = False
                    reason = "无法读取版本"
                elif version_tuple(version) < version_tuple(spec["min"]):
                    compatible = False
                    reason = f"需要 >= {spec['min']}，检测到 {version}"
            except (OSError, KeyError, subprocess.TimeoutExpired):
                compatible = False
                reason = "版本检测失败"
        rows.append({
            "id": adapter["id"],
            "available": available,
            "compatible": compatible,
            "version": version,
            "reason": reason,
            "command": path,
            "level": adapter.get("level"),
            "capabilities": adapter.get("capabilities", []),
        })
    return rows


def select_adapters(manifest: dict, detected: list[dict], requested: list[str]) -> list[str]:
    available = {row["id"] for row in detected if row["available"]}
    compatible = {row["id"] for row in detected if row["compatible"]}
    known = {row["id"] for row in detected}
    if requested:
        unknown = sorted(set(requested) - known)
        if unknown:
            raise ContractError(f"未知适配器：{', '.join(unknown)}")
        missing = sorted(set(requested) - available)
        if missing:
            raise ContractError(f"适配器不可用：{', '.join(missing)}")
        incompatible = sorted(set(requested) - compatible)
        if incompatible:
            detail = "; ".join(
                f"{row['id']}: {row['reason']}"
                for row in detected
                if row["id"] in incompatible
            )
            raise ContractError(f"适配器版本不兼容：{detail}")
        selected = requested
    else:
        selected = [row["id"] for row in detected if row["compatible"]]
    if "cli" not in selected:
        selected.insert(0, "cli")
    return list(dict.fromkeys(selected))


def version_tuple(value: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError(f"无法解析版本：{value}")
    return tuple(int(part) for part in match.groups())


def planned_changes(manifest: dict, selected: list[str]) -> list[str]:
    by_id = {row["id"]: row for row in manifest["adapters"]}
    changes = []
    for adapter_id in selected:
        changes.extend(str(value) for value in by_id[adapter_id].get("changes", []))
    return changes


def install_command(manifest: dict, selected: list[str], mode: str) -> list[str]:
    hosts = []
    by_id = {row["id"]: row for row in manifest["adapters"]}
    for adapter_id in selected:
        if adapter_id == "cli":
            continue
        hosts.extend(str(value) for value in by_id[adapter_id]["install_args"])
    command = [
        sys.executable,
        str(ROOT / manifest["installer"]),
    ]
    if mode == "uninstall":
        command.append("--uninstall")
    elif mode == "plan":
        command.append("--dry-run")
    command.extend(hosts)
    if not hosts:
        command.append("--cli-only")
    return command


def run_json_command(command: list[str]) -> dict:
    try:
        completed = subprocess.run(command, capture_output=True, text=True)
    except OSError as exc:
        return {"ok": False, "command": command, "error": str(exc)}
    payload = {"ok": completed.returncode == 0, "command": command,
               "exit": completed.returncode}
    if completed.stdout.strip():
        try:
            payload["result"] = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload["stdout"] = completed.stdout
    if completed.stderr.strip():
        payload["stderr"] = completed.stderr
    return payload


def verify_adapters(manifest: dict, selected: list[str]) -> dict:
    rows = []
    bin_dir = Path.home() / ".local" / "bin"
    for adapter_id in selected:
        if adapter_id == "cli":
            missing = [
                name for name in ("psup", "psup-mcp", "psupd")
                if not (bin_dir / name).is_symlink()
            ]
            rows.append({
                "id": "cli",
                "ok": not missing,
                "path": str(bin_dir),
                "missing": missing,
            })
    hosts = [adapter_id for adapter_id in selected if adapter_id != "cli"]
    if hosts:
        command = [
            sys.executable,
            str(ROOT / manifest["installer"]),
            "--list",
            "--json",
        ]
        result = run_json_command(command)
        by_id = {
            row.get("id"): row
            for row in (result.get("result") or {}).get("hosts", [])
        }
        for adapter_id in hosts:
            row = by_id.get(adapter_id) or {}
            rows.append({
                "id": adapter_id,
                "ok": bool(row.get("installed")),
                "available": bool(row.get("available")),
                "state": row.get("state"),
                "path": row.get("path"),
            })
    return {
        "ok": all(row["ok"] for row in rows),
        "adapters": rows,
    }


def verify(manifest: dict, selected: list[str]) -> dict:
    installed = Path.home() / ".local" / "bin" / "psup"
    if not installed.exists():
        return {
            "ok": False,
            "psup": str(installed),
            "error": "安装目录中没有 psup；不能把源码 checkout 当作安装成功",
            "results": [],
        }
    psup = installed
    results = []
    for case in manifest["verification"]:
        command = [str(psup), *case["command"][1:]]
        result = run_json_command(command)
        data = result.get("result", {})
        expect = case.get("expect") or {}
        checks = []
        for key, value in expect.items():
            if key == "sha256_equals_meta_sha256":
                actual = data.get("sha256") == data.get("meta_sha256")
            else:
                actual = data.get(key)
            checks.append({"name": key, "expected": value, "actual": actual,
                           "ok": actual == value})
        result["checks"] = checks
        result["ok"] = bool(result["ok"] and all(row["ok"] for row in checks))
        results.append(result)
    adapters = verify_adapters(manifest, selected)
    return {
        "ok": all(row["ok"] for row in results) and adapters["ok"],
        "psup": str(psup),
        "results": results,
        "adapters": adapters["adapters"],
    }


def render(command: list[str]) -> str:
    return shlex.join(command)


def report_base(manifest: dict, mode: str, *, trusted: bool) -> dict:
    signature = manifest.get("signature") or {}
    return {
        "schema_version": 1,
        "product": manifest["product"],
        "version": manifest["version"],
        "mode": mode,
        "platform": {
            "system": platform.system().lower(),
            "python": sys.version.split()[0],
            "home": str(Path.home()),
        },
        "source": manifest["source"],
        "signature": {
            "present": bool(signature),
            "verified": bool(signature),
            "trusted": trusted,
            "key_id": signature.get("key_id"),
        },
        "contract": manifest.get("contract"),
        "trigger": manifest["trigger"],
        "safety": manifest["safety"],
    }


def execute(args) -> tuple[dict, int]:
    manifest_path = Path(args.manifest).resolve()
    trust_path = Path(args.trust).resolve() if args.trust else None
    manifest = load_manifest(manifest_path, trust_path)
    detected = detect_adapters(manifest)
    selected = select_adapters(manifest, detected, args.adapter)
    mode = args.mode
    report = report_base(manifest, mode, trusted=trust_path is not None)
    report["detected"] = detected
    report["selected"] = selected
    report["changes"] = planned_changes(manifest, selected)
    report["skipped"] = [
        row["id"] for row in detected
        if row["available"] and row["id"] not in selected
    ]

    if mode == "verify":
        verification = verify(manifest, selected)
        report["status"] = "verified" if verification["ok"] else "failed"
        report["verification"] = verification
        report["rollback"] = [render(install_command(manifest, selected, "uninstall"))]
        report["ok"] = verification["ok"]
        return report, 0 if verification["ok"] else 1

    command = install_command(manifest, selected, mode)
    report["commands"] = {
        "install": render(install_command(manifest, selected, "apply")),
        "uninstall": render(install_command(manifest, selected, "uninstall")),
    }
    if mode == "plan":
        completed = subprocess.run(command, capture_output=True, text=True)
        report["installer"] = {
            "ok": completed.returncode == 0,
            "command": render(command),
            "exit": completed.returncode,
            "stdout": completed.stdout.strip().splitlines(),
            "stderr": completed.stderr.strip().splitlines(),
        }
        report["verification"] = []
        report["rollback"] = [report["commands"]["uninstall"]]
        report["ok"] = completed.returncode == 0
        report["status"] = "planned" if report["ok"] else "failed"
        return report, 0 if report["ok"] else 1

    completed = subprocess.run(command, capture_output=True, text=True)
    report["installer"] = {
        "ok": completed.returncode == 0,
        "command": render(command),
        "exit": completed.returncode,
        "stdout": completed.stdout.strip().splitlines(),
        "stderr": completed.stderr.strip().splitlines(),
    }
    if completed.returncode != 0:
        report["ok"] = False
        report["status"] = "failed"
        report["rollback"] = [report["commands"]["uninstall"]]
        return report, completed.returncode or 1

    if mode == "uninstall":
        report["ok"] = True
        report["status"] = "uninstalled"
        report["verification"] = []
        report["rollback"] = []
        return report, 0

    verification = verify(manifest, selected)
    report["verification"] = verification
    report["rollback"] = [report["commands"]["uninstall"]]
    report["ok"] = verification["ok"]
    report["status"] = "installed" if report["ok"] else "failed"
    return report, 0 if report["ok"] else 1


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="按 install-manifest.json 为 Agent 执行可验证安装",
        epilog="默认 --plan；只有显式 --apply 才会修改用户目录。",
    )
    ap.add_argument("--manifest", default=str(ROOT / "install-manifest.json"))
    ap.add_argument("--trust", help="独立可信公钥库路径；提供时强制验证签名身份")
    ap.add_argument("--adapter", action="append", default=[],
                    help="只选择指定适配器，可重复；cli 会自动加入")
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--plan", dest="mode", action="store_const", const="plan")
    modes.add_argument("--apply", dest="mode", action="store_const", const="apply")
    modes.add_argument("--verify", dest="mode", action="store_const", const="verify")
    modes.add_argument("--uninstall", dest="mode", action="store_const", const="uninstall")
    ap.set_defaults(mode="plan")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        report, code = execute(args)
    except ContractError as exc:
        report = {
            "schema_version": 1,
            "product": "skynet-prompt",
            "mode": args.mode,
            "ok": False,
            "status": "contract-error",
            "error": str(exc),
        }
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
