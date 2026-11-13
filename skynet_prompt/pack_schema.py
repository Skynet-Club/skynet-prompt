"""Prompt Pack v2 的结构契约。

这里只做确定性结构校验，不负责签名、网络或业务发布决策。
"""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

SCHEMA_VERSION = 2
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
CHANNELS = {"dev", "canary", "stable"}
REDISTRIBUTION = {"excerpt-only", "full-text"}
RIGHTS_BASES = {"short-quotation-with-attribution", "explicit-license"}
VERDICTS = {"verbatim", "paraphrase", "unverified"}
REVIEW_STATES = {"unreviewed", "reviewed"}
SAFETY_REVIEW_STATES = {"unreviewed", "reviewed", "rejected"}
SAFETY_STATES = {"unreviewed", "passed", "needs-review", "rejected"}


class PackSchemaError(ValueError):
    pass


def _require(mapping: dict, keys: tuple[str, ...], where: str) -> None:
    missing = [key for key in keys if key not in mapping or mapping[key] in (None, "")]
    if missing:
        raise PackSchemaError(f"{where} 缺少字段：{', '.join(missing)}")


def _digest(value: str, where: str) -> None:
    if not isinstance(value, str) or not DIGEST_RE.fullmatch(value):
        raise PackSchemaError(f"{where} 必须是 64 位小写 SHA-256")


def _time(value: str, where: str) -> None:
    if not isinstance(value, str):
        raise PackSchemaError(f"{where} 必须是 ISO-8601 字符串")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PackSchemaError(f"{where} 不是有效时间：{value}") from exc


def _url(value: str, where: str) -> None:
    parsed = urlparse(value) if isinstance(value, str) else None
    if not parsed or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PackSchemaError(f"{where} 必须是 HTTP/HTTPS URL")


def validate_manifest(manifest: dict, items_sha256: str) -> None:
    """校验单个 v2 manifest，并确认声明的正文摘要与文件一致。"""
    if not isinstance(manifest, dict):
        raise PackSchemaError("Pack manifest 必须是对象")
    _require(
        manifest,
        (
            "schema_version", "id", "name", "version", "channel", "published_at",
            "items", "sha256", "digest", "publisher", "min_client_version",
            "license_summary", "require_evidence",
        ),
        "Pack manifest",
    )
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise PackSchemaError("Pack manifest schema_version 必须是 2")
    if manifest["channel"] not in CHANNELS:
        raise PackSchemaError(f"未知发布通道：{manifest['channel']}")
    if manifest["items"] != "prompts.json":
        raise PackSchemaError("v2 条目文件必须命名为 prompts.json")
    _time(manifest["published_at"], "published_at")
    _digest(manifest["sha256"], "sha256")
    _digest(manifest["digest"], "digest")
    if manifest["sha256"] != items_sha256 or manifest["digest"] != items_sha256:
        raise PackSchemaError("manifest sha256/digest 与实际 prompts.json 不一致")
    publisher = manifest["publisher"]
    if not isinstance(publisher, dict):
        raise PackSchemaError("publisher 必须是对象")
    _require(publisher, ("id", "name"), "publisher")
    summary = manifest["license_summary"]
    if not isinstance(summary, dict):
        raise PackSchemaError("license_summary 必须是对象")
    _require(summary, ("default", "redistribution"), "license_summary")
    if summary["redistribution"] not in REDISTRIBUTION:
        raise PackSchemaError(f"未知 license_summary.redistribution={summary['redistribution']!r}")
    signature = manifest.get("signature")
    if signature is not None:
        if not isinstance(signature, dict):
            raise PackSchemaError("signature 必须是对象或 null")
        _require(
            signature,
            ("algorithm", "key_id", "public_key_pem", "value"),
            "signature",
        )
        if signature["algorithm"] != "ed25519":
            raise PackSchemaError("signature.algorithm 必须是 ed25519")
    if manifest["require_evidence"] is not True:
        raise PackSchemaError("v2 Pack 必须设置 require_evidence=true")


def validate_items(payload: dict) -> list[dict]:
    """校验 v2 prompts.json，并返回条目副本。"""
    if not isinstance(payload, dict):
        raise PackSchemaError("prompts.json 顶层必须是对象")
    _require(payload, ("version", "count", "items"), "prompts.json")
    items = payload["items"]
    if not isinstance(items, list) or not items:
        raise PackSchemaError("v2 Pack 必须包含非空 items")
    if not isinstance(payload["count"], int) or payload["count"] != len(items):
        raise PackSchemaError("prompts.json count 与条目数不一致")

    seen: set[str] = set()
    clean: list[dict] = []
    for index, item in enumerate(items, 1):
        where = f"条目 {index}"
        if not isinstance(item, dict):
            raise PackSchemaError(f"{where} 必须是对象")
        _require(
            item,
            (
                "id", "cat", "author", "date", "url", "en", "zh",
                "source", "evidence", "review", "safety", "insertion",
            ),
            where,
        )
        item_id = item["id"]
        if not isinstance(item_id, str):
            raise PackSchemaError(f"{where}.id 必须是字符串")
        if item_id in seen:
            raise PackSchemaError(f"重复条目 id：{item_id}")
        seen.add(item_id)
        _url(item["url"], f"{item_id}.url")

        source = item["source"]
        if not isinstance(source, dict):
            raise PackSchemaError(f"{item_id}.source 必须是对象")
        _require(
            source,
            (
                "quote", "url", "author", "published_at", "language",
                "license", "rights_basis", "redistribution", "snapshot_sha256",
            ),
            f"{item_id}.source",
        )
        _url(source["url"], f"{item_id}.source.url")
        if source["rights_basis"] not in RIGHTS_BASES:
            raise PackSchemaError(f"{item_id}.source.rights_basis 无效")
        if source["redistribution"] not in REDISTRIBUTION:
            raise PackSchemaError(f"{item_id}.source.redistribution 无效")
        _digest(source["snapshot_sha256"], f"{item_id}.source.snapshot_sha256")

        evidence = item["evidence"]
        if not isinstance(evidence, dict):
            raise PackSchemaError(f"{item_id}.evidence 必须是对象")
        _require(evidence, ("verdict", "checked_at"), f"{item_id}.evidence")
        if evidence["verdict"] not in VERDICTS:
            raise PackSchemaError(f"{item_id}.evidence.verdict 无效")
        _time(evidence["checked_at"], f"{item_id}.evidence.checked_at")

        review = item["review"]
        if not isinstance(review, dict):
            raise PackSchemaError(f"{item_id}.review 必须是对象")
        _require(review, ("source", "translation", "safety"), f"{item_id}.review")
        if review["source"] not in REVIEW_STATES:
            raise PackSchemaError(f"{item_id}.review.source 无效")
        if review["translation"] not in REVIEW_STATES:
            raise PackSchemaError(f"{item_id}.review.translation 无效")
        if review["safety"] not in SAFETY_REVIEW_STATES:
            raise PackSchemaError(f"{item_id}.review.safety 无效")

        safety = item["safety"]
        if not isinstance(safety, dict):
            raise PackSchemaError(f"{item_id}.safety 必须是对象")
        _require(safety, ("status", "flags"), f"{item_id}.safety")
        if safety["status"] not in SAFETY_STATES:
            raise PackSchemaError(f"{item_id}.safety.status 无效")
        if not isinstance(safety["flags"], list) or not all(
            isinstance(flag, str) for flag in safety["flags"]
        ):
            raise PackSchemaError(f"{item_id}.safety.flags 必须是字符串数组")

        insertion = item["insertion"]
        if not isinstance(insertion, dict) or insertion.get("policy") != "exact-zh":
            raise PackSchemaError(f"{item_id}.insertion.policy 必须是 exact-zh")
        translations = item.get("translations", [])
        if not isinstance(translations, list):
            raise PackSchemaError(f"{item_id}.translations 必须是数组")
        languages = set()
        for translation in translations:
            if not isinstance(translation, dict):
                raise PackSchemaError(f"{item_id}.translations 条目必须是对象")
            _require(translation, ("language", "text", "status"), f"{item_id}.translations")
            if translation["status"] not in {"machine", "unreviewed", "reviewed"}:
                raise PackSchemaError(f"{item_id}.translations.status 无效")
            if translation["language"] in languages:
                raise PackSchemaError(f"{item_id}.translations 语言重复")
            languages.add(translation["language"])
        clean.append(dict(item))
    return clean


__all__ = [
    "PackSchemaError",
    "SCHEMA_VERSION",
    "validate_items",
    "validate_manifest",
]
