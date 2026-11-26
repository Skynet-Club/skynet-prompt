"""官方提示词包：加载、校验、搜索、读取和审计。

只有一份数据源：``data/prompts.json``。``meta.json`` 只记录版本、条数、
sha256 和场景统计；两边的条数与 sha256 必须一致。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data"
CATS = [
    ("加目标", "goal"),
    ("加深度", "depth"),
    ("加广度", "breadth"),
    ("加约束", "constraint"),
    ("加证据", "evidence"),
    ("加检验", "check"),
    ("加读者", "reader"),
    ("加执行", "execution"),
    ("加时间", "time"),
]
CATS_EN = {
    "goal": "Goal",
    "depth": "Depth",
    "breadth": "Breadth",
    "constraint": "Constraints",
    "evidence": "Evidence",
    "check": "Check",
    "reader": "Reader",
    "execution": "Execution",
    "time": "Time",
}
DISPLAY = {key: name for name, key in CATS}
REQUIRED = ("id", "cat", "author", "date", "url", "en", "zh")
EVIDENCE_VERDICTS = {"verbatim", "paraphrase", "unverified"}
RIGHTS_BASES = {"short-quotation-with-attribution", "explicit-license"}
DISTRIBUTION = {"excerpt-only", "full-text"}


class PromptDataError(RuntimeError):
    """数据缺失、损坏或不符合契约。"""


def data_dir() -> Path:
    return Path(os.environ.get("SKYNET_PROMPT_DATA", DEFAULT_DATA)).expanduser()


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


class PromptCatalog:
    """一份不可变数据的只读视图。"""

    def __init__(self, path: Path | None = None) -> None:
        self.dir = Path(path).expanduser() if path else data_dir()
        self.path = self.dir / "prompts.json"
        self.meta_path = self.dir / "meta.json"
        self._items: list[dict] | None = None
        self._meta: dict | None = None
        self.sha256 = ""

    def load(self) -> "PromptCatalog":
        if self._items is not None:
            return self
        try:
            body = self.path.read_bytes()
            payload = json.loads(body)
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise PromptDataError(f"数据不可读：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise PromptDataError(f"JSON 解析失败：{exc}") from exc
        if not isinstance(payload, dict) or not isinstance(meta, dict):
            raise PromptDataError("数据必须是 JSON 对象")
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            raise PromptDataError("没有加载到任何提示词")
        digest = _sha256(body)
        if meta.get("sha256") != digest:
            raise PromptDataError("sha256 与 meta.json 不一致")
        if meta.get("count") != len(items) or payload.get("count") != len(items):
            raise PromptDataError("条数与 meta.json 不一致")
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                raise PromptDataError("条目必须是 JSON 对象")
            missing = [field for field in REQUIRED if not item.get(field)]
            if missing:
                raise PromptDataError(f"条目 {item.get('id', '?')} 缺少字段：{missing}")
            if item["cat"] not in DISPLAY:
                raise PromptDataError(f"条目 {item['id']} 的场景不存在：{item['cat']}")
            if item["id"] in seen:
                raise PromptDataError(f"提示词 id 重复：{item['id']}")
            seen.add(item["id"])
        self._items = items
        self._meta = meta
        self.sha256 = digest
        return self

    def _ensure(self) -> None:
        if self._items is None:
            self.load()

    def items(self) -> list[dict]:
        self._ensure()
        return list(self._items or [])

    def meta(self) -> dict:
        self._ensure()
        return dict(self._meta or {})

    def packs(self) -> list[dict]:
        self._ensure()
        official = sum(
            1 for item in self._items or []
            if (item.get("evidence") or {}).get("verdict") == "verbatim"
        )
        return [{
            "id": "library",
            "name": "提示词库",
            "version": (self._meta or {}).get("version", ""),
            "count": len(self._items or []),
            "official_count": official,
            "sha256": self.sha256,
        }]

    def categories(self) -> list[dict]:
        self._ensure()
        counts = {key: 0 for _, key in CATS}
        for item in self._items or []:
            counts[item["cat"]] += 1
        return [{"key": key, "name": name, "en": CATS_EN[key], "count": counts[key]}
                for name, key in CATS]

    def search(
        self,
        query: str = "",
        category: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        self._ensure()
        if not isinstance(query, str):
            raise PromptDataError("query 必须是字符串")
        if category:
            key = category if category in DISPLAY else next(
                (k for name, k in CATS if name == category), category)
            if key not in DISPLAY:
                raise PromptDataError(f"没有 category={category}")
        else:
            key = ""
        needle = query.strip().casefold()
        rows = []
        for item in self._items or []:
            if key and item["cat"] != key:
                continue
            if needle:
                haystack = " ".join((
                    item.get("zh", ""), item.get("en", ""),
                    item.get("author", ""), DISPLAY[item["cat"]],
                )).casefold()
                if needle not in haystack:
                    continue
            rows.append(item)
        if limit is not None:
            rows = rows[:max(limit, 0)]
        return rows

    def get(self, item_id: str) -> dict:
        self._ensure()
        for item in self._items or []:
            if item["id"] == item_id:
                return item
        raise PromptDataError(f"没有 id={item_id}")

    def audit(self) -> dict:
        self._ensure()
        evidence = {verdict: 0 for verdict in sorted(EVIDENCE_VERDICTS)}
        rights = {basis: 0 for basis in sorted(RIGHTS_BASES)}
        missing: list[str] = []
        missing_rights: list[str] = []
        official_ids: set[str] = set()
        for item in self._items or []:
            verdict = (item.get("evidence") or {}).get("verdict")
            if verdict in evidence:
                evidence[verdict] += 1
            else:
                evidence["unverified"] += 1
                missing.append(item["id"])
            if verdict == "verbatim":
                official_ids.add(item["id"])
            source = item.get("source") or {}
            if (
                source.get("rights_basis") not in RIGHTS_BASES
                or source.get("redistribution") not in DISTRIBUTION
                or not source.get("license")
            ):
                missing_rights.append(item["id"])
            else:
                rights[source["rights_basis"]] += 1
        # 正式包只判断 verbatim 子集；实验区的 paraphrase/unverified 不阻塞发布。
        official_ready = bool(official_ids) and not (
            (set(missing) | set(missing_rights)) & official_ids
        )
        return {
            "ok": not missing and not missing_rights,
            "official_ready": official_ready,
            "official_count": len(official_ids),
            "count": len(self._items or []),
            "evidence": evidence,
            "rights": rights,
            "missing": missing,
            "missing_rights": missing_rights,
        }


def default_catalog(path: Path | None = None) -> PromptCatalog:
    return PromptCatalog(path)
