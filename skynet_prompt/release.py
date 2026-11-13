"""可重复的 Prompt Pack 发布流水线。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .approvals import ApprovalError, verify_approval_set
from .catalog import JsonPackSource, PromptCatalog, default_catalog
from .content import verify as verify_content
from .reviews import load_ledger, validate_ledger
from .safety import RULE_VERSION, scan_item
from .source_snapshots import verify_manifest


class ReleaseError(RuntimeError):
    pass


def _git_commit(root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def release(
    root: Path,
    out: Path,
    *,
    channel: str = "dev",
    private_key: Path | None = None,
    key_id: str = "skynet-club-dev",
    approval_paths: list[Path] | None = None,
    trust_path: Path | None = None,
) -> dict:
    if channel not in {"dev", "canary", "stable"}:
        raise ReleaseError(f"未知发布通道：{channel}")
    if channel == "stable" and private_key is None:
        raise ReleaseError("stable 通道必须提供签名私钥")

    content = verify_content()
    if not content["ok"]:
        raise ReleaseError("内容冻结校验失败：" + "; ".join(content["errors"]))

    catalog = default_catalog().load()
    audit = catalog.audit()
    if audit["missing"] or audit["missing_rights"]:
        raise ReleaseError("内容证据或版权字段不完整")
    official = [
        item for item in catalog.items()
        if item["evidence"]["verdict"] in {"verbatim", "paraphrase"}
    ]
    if not official:
        raise ReleaseError("没有可发布条目")

    ledger = load_ledger(root / "reviews" / "review-ledger.json")
    validate_ledger(ledger, catalog.items())
    missing_reviews = [item["id"] for item in official if item["id"] not in ledger["items"]]
    if missing_reviews:
        raise ReleaseError("正式条目缺少审核：" + ", ".join(missing_reviews))

    snapshots = verify_manifest(
        root / "reports" / "sources" / "index.json",
        {item["url"] for item in official},
    )
    if not snapshots["ok"]:
        raise ReleaseError("来源快照校验失败：" + "; ".join(snapshots["errors"]))

    safety_rows = [
        {"id": item["id"], **scan_item(item)}
        for item in official
    ]
    unsafe = [row["id"] for row in safety_rows if row["status"] != "passed"]
    if unsafe:
        raise ReleaseError("正式条目安全扫描未通过：" + ", ".join(unsafe))

    build_check = subprocess.run(
        [sys.executable, str(root / "psup"), "build", "--check"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if build_check.returncode != 0:
        raise ReleaseError(
            "宿主产物与 content/ 不一致：" + (build_check.stderr or build_check.stdout).strip()
        )

    export_command = [
        sys.executable,
        str(root / "scripts" / "export_official.py"),
        "--out",
        str(out),
        "--channel",
        channel,
        "--key-id",
        key_id,
    ]
    if private_key:
        export_command.extend(["--private-key", str(private_key)])
    export = subprocess.run(
        export_command,
        cwd=root,
        capture_output=True,
        text=True,
    )
    if export.returncode != 0:
        raise ReleaseError(
            "v2 导出失败：" + (export.stderr or export.stdout).strip()
        )

    pack = JsonPackSource(out).load()
    if len(pack.items) != len(official):
        raise ReleaseError("导出后条目数量不一致")
    PromptCatalog([JsonPackSource(out)]).load()
    approval_paths = approval_paths or []
    approval_result = None
    if approval_paths or channel == "stable":
        if not approval_paths:
            raise ReleaseError("stable 通道必须提供 reviewer 与 publisher 审批")
        approval_trust = trust_path or (root / "trust" / "keys.json")
        try:
            approval_result = verify_approval_set(
                approval_paths,
                approval_trust,
                {
                    "pack_id": pack.id,
                    "version": pack.version,
                    "pack_sha256": pack.sha256,
                    "item_count": len(pack.items),
                },
            )
        except ApprovalError as exc:
            raise ReleaseError(str(exc)) from exc

    report = {
        "ok": True,
        "channel": channel,
        "version": pack.version,
        "pack_id": pack.id,
        "item_count": len(pack.items),
        "pack_sha256": pack.sha256,
        "content_digest": content["digest"],
        "evidence": audit["evidence"],
        "rights": audit["rights"],
        "reviewed": len(ledger["items"]),
        "source_snapshots": snapshots["checked"],
        "safety_rule_version": RULE_VERSION,
        "signed": bool(
            json.loads((out / "pack.json").read_text(encoding="utf-8")).get("signature")
        ),
        "approvals": approval_result,
        "git_commit": _git_commit(root),
        "built_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
    }
    (out / "release-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


__all__ = ["ReleaseError", "release"]
