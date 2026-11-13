"""核对每条原文是否真的出现在它标注的链接里（DC-04 / DC-05 的机器部分）。

用法：
    python3 scripts/check_sources.py            # 只比本地已抓的源文件
    python3 scripts/check_sources.py --fetch    # 先抓再接（需要网络）

源文件放 reports/sources/，索引在 reports/sources/index.json（url → 文件名 + 抓取方式）。
为什么要有本地索引：x.com 从部分网络不可达，抓取往往得换通道（例如浏览器/web_extract），
把抓到的文本落盘再比对，报告才是可复现的——否则每次跑出来的结论都不一样。

判定口径：原文里用 "…" 连接的片段必须逐个都能在源文本里找到（去掉标点差异后）。
    ok        全部片段命中
    partial   部分命中（通常是表里把两句拼在一起，或源页被截断）
    missing   一个都没命中
    no_source 本地没有这条例子的源文件，没核过（不猜）
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skynet_prompt.source_snapshots import load_manifest  # noqa: E402

SOURCES = ROOT / "reports" / "sources"
MIN_FRAGMENT = 12


def plain(text: str) -> str:
    """把 HTML / markdown 揉成可比对的纯文本。"""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u00a0", " ")
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def fragments(en: str) -> list[str]:
    parts = [p for p in re.split(r"…+|\.\.\.", en) if p.strip()]
    out = []
    for part in parts:
        norm = plain(part)
        if len(norm) >= MIN_FRAGMENT:
            out.append(norm)
    return out or [plain(en)]


def strip_reference_noise(item: dict) -> str:
    """表里的原文可能带省略号拼接；比对时按片段算，别整段比。"""
    return item.get("en", "")


def check() -> dict:
    items = json.loads((ROOT / "data" / "prompts.json").read_text(encoding="utf-8"))["items"]
    index_path = SOURCES / "index.json"
    index = load_manifest(index_path)["sources"] if index_path.exists() else {}

    cache: dict[str, str] = {}
    rows = []
    for item in items:
        url = item.get("url", "")
        entry = index.get(url) or {}
        name = entry.get("file")
        if not name or not (SOURCES / name).exists():
            rows.append({"id": item["id"], "url": url, "verdict": "no_source",
                         "fragments": 0, "hit": 0, "via": None})
            continue
        if name not in cache:
            cache[name] = plain((SOURCES / name).read_text(encoding="utf-8", errors="ignore"))
        source = cache[name]
        frags = fragments(strip_reference_noise(item))
        hit = sum(1 for f in frags if f in source)
        verdict = "ok" if hit == len(frags) else ("partial" if hit else "missing")
        rows.append({"id": item["id"], "url": url, "verdict": verdict,
                     "fragments": len(frags), "hit": hit, "via": entry.get("via")})

    total = len(rows)
    summary = {
        "checked_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "total": total,
        "ok": sum(1 for r in rows if r["verdict"] == "ok"),
        "partial": sum(1 for r in rows if r["verdict"] == "partial"),
        "missing": sum(1 for r in rows if r["verdict"] == "missing"),
        "no_source": sum(1 for r in rows if r["verdict"] == "no_source"),
        "by_url": {},
        "rows": rows,
    }
    for row in rows:
        slot = summary["by_url"].setdefault(row["url"], {"ok": 0, "partial": 0,
                                                         "missing": 0, "no_source": 0})
        slot[row["verdict"]] += 1
    return summary


def fetch_missing() -> None:
    """给没有源文件的链接补抓。抓不到就留空，不编。"""
    import urllib.request

    items = json.loads((ROOT / "data" / "prompts.json").read_text(encoding="utf-8"))["items"]
    index_path = SOURCES / "index.json"
    manifest = load_manifest(index_path) if index_path.exists() else {
        "schema_version": 1,
        "generated_at": None,
        "sources": {},
    }
    index = manifest["sources"]
    SOURCES.mkdir(parents=True, exist_ok=True)
    for url in {i["url"] for i in items}:
        if (index.get(url) or {}).get("file"):
            continue
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", url.split("//", 1)[-1])[:60].strip("-")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 psup-source-check"})
            body = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
            path = SOURCES / f"{slug}.html"
            path.write_text(body, encoding="utf-8")
            data = path.read_bytes()
            index[url] = {
                "file": path.name,
                "via": "urllib",
                "fetched_at": datetime.now(timezone(timedelta(hours=8))).isoformat(
                    timespec="seconds"
                ),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "media_type": "text/html",
                "ok": True,
            }
            print(f"抓取成功 {url}")
        except Exception as exc:  # noqa: BLE001
            index[url] = {"file": None, "via": None, "error": str(exc)[:120]}
            print(f"抓取失败 {url} → {type(exc).__name__}")
    manifest["schema_version"] = 1
    manifest["generated_at"] = datetime.now(timezone(timedelta(hours=8))).isoformat(
        timespec="seconds"
    )
    manifest["sources"] = index
    index_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="先抓没有本地源的链接")
    args = ap.parse_args(argv)
    if args.fetch:
        fetch_missing()
    summary = check()
    out = ROOT / "reports" / "source-check.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"核对时间 {summary['checked_at']}")
    print(f"共 {summary['total']} 条：全文命中 {summary['ok']} · 部分命中 {summary['partial']}"
          f" · 未命中 {summary['missing']} · 无源文件 {summary['no_source']}")
    for url, slot in summary["by_url"].items():
        print(f"  {slot}  {url}")
    bad = [r for r in summary["rows"] if r["verdict"] in ("partial", "missing")]
    for row in bad:
        print(f"  ! {row['verdict']:8s} {row['id']}  {row['hit']}/{row['fragments']}  {row['url']}")
    print(f"报告 {out}")
    return 0 if summary["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
