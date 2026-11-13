"""提示词包目录：内置包、本地扩展包和未来数据源共用的加载接口。

``PromptSource`` 是稳定扩展点：任何对象只要实现 ``load() -> PromptPack``，
就可以注册进 ``PromptCatalog``。磁盘包只是一种现成实现。
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .pack_schema import PackSchemaError, validate_items, validate_manifest

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data"

CATS = [
    ("要结果", "outcome"),
    ("先想清楚", "think_first"),
    ("定格式", "format"),
    ("定验收", "verify"),
    ("换视角", "perspective"),
    ("用高手的方法", "expert_method"),
    ("换形态", "form"),
    ("砍掉多余的", "cut"),
    ("别碰旁边的", "boundary"),
]
DISPLAY = {key: name for name, key in CATS}

REQUIRED_ITEM_FIELDS = ("id", "cat", "author", "date", "url", "en", "zh")
EVIDENCE_VERDICTS = {"verbatim", "paraphrase", "unverified"}
RIGHTS_BASES = {"short-quotation-with-attribution", "explicit-license"}
DISTRIBUTION_POLICIES = {"excerpt-only", "full-text"}


class PromptDataError(RuntimeError):
    """提示词包缺失、损坏或不符合契约。"""


@dataclass
class PromptPack:
    """一个已经加载的提示词包。"""

    id: str
    name: str
    version: str
    items: list[dict]
    sha256: str
    path: Path | None = None
    meta: dict = field(default_factory=dict)
    require_evidence: bool = False


class PromptSource(Protocol):
    """未来数据源需要实现的最小接口。"""

    def load(self) -> PromptPack:
        ...


def data_dir() -> Path:
    """内置数据目录；保留两个旧环境变量以兼容已有安装。"""
    for name in ("SKYNET_PROMPT_DATA", "PROMPT_SUPPLEMENT_DATA"):
        value = os.environ.get(name)
        if value:
            return Path(value).expanduser()
    return DEFAULT_DATA


def _read_json(path: Path, label: str) -> dict:
    if not path.exists():
        raise PromptDataError(f"{label}缺失：{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromptDataError(f"{label}损坏：{path}（{exc}）") from exc
    if not isinstance(payload, dict):
        raise PromptDataError(f"{label}格式错误：顶层必须是对象（{path}）")
    return payload


def _load_items(path: Path) -> tuple[list[dict], dict]:
    payload = _read_json(path, "数据文件")
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise PromptDataError(f"数据文件是空的：{path}")
    declared = payload.get("count")
    if isinstance(declared, int) and declared != len(items):
        raise PromptDataError(
            f"数据文件计数不一致：{path} 有 {len(items)} 条，声明 {declared} 条"
        )
    return items, payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_pack(pack: PromptPack) -> PromptPack:
    if not pack.id.strip():
        raise PromptDataError("提示词包 id 不能为空")
    if not pack.name.strip():
        raise PromptDataError(f"提示词包 {pack.id} 缺少 name")
    if not pack.items:
        raise PromptDataError(f"提示词包 {pack.id} 没有条目")

    seen: set[str] = set()
    clean_items: list[dict] = []
    for index, item in enumerate(pack.items, 1):
        if not isinstance(item, dict):
            raise PromptDataError(f"提示词包 {pack.id} 第 {index} 条不是对象")
        missing = [key for key in REQUIRED_ITEM_FIELDS if not item.get(key)]
        if missing:
            raise PromptDataError(
                f"提示词包 {pack.id} 第 {index} 条缺少字段：{', '.join(missing)}"
            )
        item_id = str(item["id"])
        if item_id in seen:
            raise PromptDataError(f"提示词包 {pack.id} 内有重复 id：{item_id}")
        if item["cat"] not in DISPLAY:
            raise PromptDataError(
                f"提示词包 {pack.id} 的 {item_id} 使用了未知类目：{item['cat']}"
            )
        if pack.require_evidence:
            source = item.get("source")
            evidence = item.get("evidence")
            if not isinstance(source, dict) or not source.get("quote") or not source.get("url"):
                raise PromptDataError(
                    f"提示词包 {pack.id} 的 {item_id} 缺少 source.quote/source.url"
                )
            missing_rights = [
                key for key in ("license", "rights_basis", "redistribution")
                if not source.get(key)
            ]
            if missing_rights:
                raise PromptDataError(
                    f"提示词包 {pack.id} 的 {item_id} 缺少版权字段："
                    + ", ".join(missing_rights)
                )
            if source["rights_basis"] not in RIGHTS_BASES:
                raise PromptDataError(
                    f"提示词包 {pack.id} 的 {item_id} 使用未知 rights_basis="
                    f"{source['rights_basis']!r}"
                )
            if source["redistribution"] not in DISTRIBUTION_POLICIES:
                raise PromptDataError(
                    f"提示词包 {pack.id} 的 {item_id} 使用未知 redistribution="
                    f"{source['redistribution']!r}"
                )
            if not isinstance(evidence, dict):
                raise PromptDataError(f"提示词包 {pack.id} 的 {item_id} 缺少 evidence")
            verdict = evidence.get("verdict")
            if verdict not in EVIDENCE_VERDICTS:
                raise PromptDataError(
                    f"提示词包 {pack.id} 的 {item_id} evidence.verdict 无效：{verdict}"
                )
            if not evidence.get("checked_at"):
                raise PromptDataError(
                    f"提示词包 {pack.id} 的 {item_id} 缺少 evidence.checked_at"
                )
        seen.add(item_id)
        clean_items.append(dict(item))

    pack.items = clean_items
    return pack


class BuiltinPromptSource:
    """仓库自带数据包，兼容现有 prompts.json/meta.json 布局。"""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or data_dir()

    def load(self) -> PromptPack:
        prompt_path = self.root / "prompts.json"
        items, payload = _load_items(prompt_path)
        meta = {}
        meta_path = self.root / "meta.json"
        if meta_path.exists():
            meta = _read_json(meta_path, "元数据文件")
        digest = _sha256(prompt_path)
        declared = meta.get("sha256")
        if declared and declared != digest:
            raise PromptDataError(
                f"内置数据 sha256 不匹配：{prompt_path} 实际 {digest}，声明 {declared}"
            )
        return PromptPack(
            id=str(meta.get("id") or "builtin"),
            name=str(meta.get("name") or "内置提示词包"),
            version=str(meta.get("version") or payload.get("version") or ""),
            items=items,
            sha256=digest,
            path=prompt_path,
            meta=meta,
            require_evidence=bool(meta.get("require_evidence")),
        )


class JsonPackSource:
    """从 ``pack.json`` 描述的本地目录加载一个扩展包。"""

    def __init__(self, manifest: Path | str) -> None:
        path = Path(manifest).expanduser()
        self.manifest = path / "pack.json" if path.is_dir() else path

    def load(self) -> PromptPack:
        manifest = _read_json(self.manifest, "提示词包清单")
        schema_version = manifest.get("schema_version", 1)
        if schema_version not in {1, 2}:
            raise PromptDataError(
                f"不支持的提示词包 schema_version={schema_version}：{self.manifest}"
            )
        pack_id = str(manifest.get("id") or "").strip()
        if not pack_id:
            raise PromptDataError(f"提示词包清单缺少 id：{self.manifest}")
        item_path = self.manifest.parent / str(manifest.get("items") or "prompts.json")
        items, payload = _load_items(item_path)
        digest = _sha256(item_path)
        if schema_version == 2:
            try:
                validate_manifest(manifest, digest)
                items = validate_items({"version": manifest["version"], "count": len(items), "items": items})
            except PackSchemaError as exc:
                raise PromptDataError(
                    f"提示词包 {pack_id} 不符合 v2 Schema：{exc}（{self.manifest}）"
                ) from exc
        declared = manifest.get("sha256")
        if declared and declared != digest:
            raise PromptDataError(
                f"提示词包 {pack_id} 的 sha256 不匹配：实际 {digest}，声明 {declared}"
            )
        return PromptPack(
            id=pack_id,
            name=str(manifest.get("name") or pack_id),
            version=str(manifest.get("version") or payload.get("version") or ""),
            items=items,
            sha256=digest,
            path=item_path,
            meta=manifest,
            require_evidence=bool(manifest.get("require_evidence")),
        )


class PromptCatalog:
    """把多个来源合并成一个只读目录，并拒绝重复包 id / 条目 id。"""

    def __init__(self, sources: list[PromptSource] | None = None) -> None:
        self._sources = list(sources or [])
        self._packs: list[PromptPack] | None = None
        self._items: list[dict] | None = None
        self._item_packs: dict[str, str] = {}

    def register(self, source: PromptSource) -> None:
        self._sources.append(source)
        self._packs = None
        self._items = None
        self._item_packs = {}

    def load(self) -> "PromptCatalog":
        packs: list[PromptPack] = []
        items: list[dict] = []
        item_packs: dict[str, str] = {}
        pack_ids: set[str] = set()

        for source in self._sources:
            pack = _validate_pack(source.load())
            if pack.id in pack_ids:
                raise PromptDataError(f"提示词包 id 重复：{pack.id}")
            pack_ids.add(pack.id)
            for item in pack.items:
                item_id = str(item["id"])
                if item_id in item_packs:
                    raise PromptDataError(
                        f"提示词 id 重复：{item_id}（{item_packs[item_id]} 与 {pack.id}）"
                    )
                item_packs[item_id] = pack.id
                items.append(item)
            packs.append(pack)

        if not items:
            raise PromptDataError("没有加载到任何提示词")
        self._packs = packs
        self._items = items
        self._item_packs = item_packs
        return self

    def _ensure_loaded(self) -> None:
        if self._packs is None or self._items is None:
            self.load()

    def items(self) -> list[dict]:
        self._ensure_loaded()
        return [dict(item) for item in self._items or []]

    def packs(self) -> list[PromptPack]:
        self._ensure_loaded()
        return list(self._packs or [])

    def pack_id(self, item_id: str) -> str:
        self._ensure_loaded()
        try:
            return self._item_packs[item_id]
        except KeyError as exc:
            raise PromptDataError(f"没有 id={item_id}") from exc

    def audit(self) -> dict:
        """汇总结构化证据与版权字段；不把旧字段猜成已核实。"""
        self._ensure_loaded()
        counts = {verdict: 0 for verdict in sorted(EVIDENCE_VERDICTS)}
        rights_counts = {rights: 0 for rights in sorted(RIGHTS_BASES)}
        missing: list[str] = []
        missing_rights: list[str] = []
        for item in self._items or []:
            evidence = item.get("evidence")
            verdict = evidence.get("verdict") if isinstance(evidence, dict) else None
            if verdict in counts:
                counts[verdict] += 1
            else:
                counts["unverified"] += 1
                missing.append(str(item["id"]))
            source = item.get("source")
            rights_basis = source.get("rights_basis") if isinstance(source, dict) else None
            redistribution = source.get("redistribution") if isinstance(source, dict) else None
            if (
                rights_basis not in RIGHTS_BASES
                or redistribution not in DISTRIBUTION_POLICIES
                or not source.get("license")
            ):
                missing_rights.append(str(item["id"]))
            else:
                rights_counts[rights_basis] += 1
        official_ready = (
            not missing
            and not missing_rights
            and counts["unverified"] == 0
        )
        return {
            "ok": not missing and not missing_rights,
            "official_ready": official_ready,
            "count": len(self._items or []),
            "evidence": counts,
            "rights": rights_counts,
            "missing": missing,
            "missing_rights": missing_rights,
            "packs": [
                {
                    "id": pack.id,
                    "require_evidence": pack.require_evidence,
                    "count": len(pack.items),
                }
                for pack in self._packs or []
            ],
        }


def default_catalog() -> PromptCatalog:
    """内置包 + ``SKYNET_PROMPT_PACKS`` 中列出的扩展包。"""
    sources: list[PromptSource] = [BuiltinPromptSource()]
    raw_packs = os.environ.get("SKYNET_PROMPT_PACKS", "")
    for raw in raw_packs.split(os.pathsep):
        if raw.strip():
            sources.append(JsonPackSource(raw.strip()))
    return PromptCatalog(sources)
