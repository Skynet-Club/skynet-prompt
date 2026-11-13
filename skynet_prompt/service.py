"""CLI、MCP 和未来 HTTP 共用的只读查询服务。"""

from __future__ import annotations

from .catalog import DISPLAY, PromptCatalog, PromptDataError, default_catalog


class PromptServiceError(ValueError):
    pass


class PromptService:
    def __init__(self, catalog: PromptCatalog | None = None) -> None:
        self.catalog = (catalog or default_catalog()).load()

    def items(self) -> list[dict]:
        return self.catalog.items()

    def packs(self) -> list[dict]:
        return [
            {
                "id": pack.id,
                "name": pack.name,
                "version": pack.version,
                "count": len(pack.items),
                "sha256": pack.sha256,
                "path": str(pack.path or ""),
            }
            for pack in self.catalog.packs()
        ]

    def categories(self) -> list[dict]:
        counts = {key: 0 for key in DISPLAY}
        for item in self.items():
            if item.get("cat") in counts:
                counts[item["cat"]] += 1
        return [
            {"key": key, "name": name, "count": counts[key]}
            for key, name in DISPLAY.items()
        ]

    @staticmethod
    def _haystack(item: dict) -> str:
        return " ".join((
            item.get("zh", ""),
            item.get("en", ""),
            item.get("author", ""),
            DISPLAY.get(item.get("cat", ""), ""),
        )).casefold()

    def search(
        self,
        query: str = "",
        *,
        category: str | None = None,
        pack: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        words = query.casefold().split()
        pack_ids = {row["id"] for row in self.packs()}
        if pack and pack not in pack_ids:
            raise PromptServiceError(f"没有提示词包 {pack}")
        if category:
            category_key = category if category in DISPLAY else next(
                (key for key, name in DISPLAY.items() if name == category),
                "",
            )
            if not category_key:
                raise PromptServiceError(f"未知类目 {category}")
        else:
            category_key = ""

        rows = []
        for item in self.items():
            if category_key and item.get("cat") != category_key:
                continue
            if pack and self.catalog.pack_id(item["id"]) != pack:
                continue
            text = self._haystack(item)
            if all(word in text for word in words):
                rows.append(item)
        if limit is not None:
            if limit < 1:
                raise PromptServiceError("limit 必须大于 0")
            rows = rows[:limit]
        return rows

    def get(self, item_id: str) -> dict:
        for item in self.items():
            if item["id"] == item_id:
                return item
        raise PromptServiceError(f"没有 id={item_id}")

    def compose(
        self,
        item_ids: list[str],
        *,
        field: str = "zh",
        separator: str = "\n\n",
    ) -> dict:
        if field not in {"zh", "en"}:
            raise PromptServiceError("field 只能是 zh 或 en")
        if not item_ids:
            raise PromptServiceError("至少需要一个 id")
        items = [self.get(item_id) for item_id in item_ids]
        return {
            "ids": item_ids,
            "field": field,
            "text": separator.join(str(item[field]) for item in items),
        }

    def audit(self) -> dict:
        return self.catalog.audit()


__all__ = ["PromptDataError", "PromptService", "PromptServiceError"]
