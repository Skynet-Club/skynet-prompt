"""TUI 抽屉的数据入口：只做加载，不持有状态。"""

from __future__ import annotations

from .catalog import CATS, DISPLAY, data_dir, default_catalog


def load() -> tuple[list[dict], dict]:
    catalog = default_catalog().load()
    return catalog.items(), {"pack": catalog.packs()[0]}


__all__ = ["CATS", "DISPLAY", "data_dir", "load"]
