"""把 Club / 飞书编辑工作区导出的 ndjson 冻结成兼容镜像 data/。

编辑工作区不是运行时真相源；历史数据经 freeze_content.py 转为逐条发布快照后，
content/ 才是发布与构建真相，data/ 只用于旧客户端兼容。

用法：
    python3 scripts/freeze.py scripts/raw-20261111.ndjson

导出方式（需要 lark-cli，非运行依赖）：
    lark-cli base +record-list --base-token Mzjpb8mWoawYL9s0IuSccO4znVf \
        --table-id tblnXF32xJGMYjx1 --format ndjson --output raw.ndjson

不联网、不改表，只读本地文件后落盘；落盘顺序固定，同样的输入得同样的 sha256。
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# 表里的「共性分类」→ 代码里的内部键 + 抽屉里的显示名。一对一，顺序即菜单顺序。
CATS = [
    ("抬高目标", "outcome", "要结果"),
    ("先想再做", "think_first", "先想清楚"),
    ("固定形式", "format", "定格式"),
    ("先验证再算完", "verify", "定验收"),
    ("换视角与阵容", "perspective", "换视角"),
    ("按高手的方法做", "expert_method", "用高手的方法"),
    ("换输出形态", "form", "换形态"),
    ("简单优先", "cut", "砍掉多余的"),
    ("只改必须改的", "boundary", "别碰旁边的"),
]
CAT_KEY = {zh: (key, disp) for zh, key, disp in CATS}
CAT_ORDER = {key: i for i, (_, key, _) in enumerate(CATS)}
AUTHOR_CODE = {"Karpathy": "kp", "Felix Rieseberg": "fx", "Ethan Mollick": "em"}

# 「他人整理」的 12 条实际出自这份 CLAUDE.md 仓库（四条原则的整理版）。表里给的是那条被整理
# 的推文链接，但推文里没有这些句子，所以链接以仓库为准——性质仍是「他人整理」，不改。
KARPATHY_SKILLS_REPO = "https://github.com/forrestchang/andrej-karpathy-skills"


def one(row: dict, field: str) -> str:
    v = row.get(field)
    if isinstance(v, list):
        v = v[0] if v else ""
    return (v or "").strip()


def main(src: str) -> int:
    rows = [json.loads(line) for line in Path(src).read_text().splitlines() if line.strip()]
    items, problems = [], []
    for row in rows:
        en, zh = one(row, "原文（英文逐字）"), one(row, "中文直译")
        cat_raw, author = one(row, "共性分类"), one(row, "作者")
        url, date = one(row, "链接"), one(row, "日期")[:10].replace("/", "-")
        rid = row.get("record_id", "")
        if not (en and zh and cat_raw and author and url):
            problems.append(f"{rid}: 字段不全")
            continue
        if cat_raw not in CAT_KEY:
            problems.append(f"{rid}: 未知分类 {cat_raw}")
            continue
        key, _disp = CAT_KEY[cat_raw]
        nature_raw = one(row, "性质")
        if nature_raw == "他人整理":
            url = KARPATHY_SKILLS_REPO
        items.append({
            "id": f"{AUTHOR_CODE.get(author, 'xx')}-{key}-{len(items) + 1:02d}",
            "cat": key,
            "author": author,
            "date": date,
            "url": url,
            "en": en,
            "zh": zh,
            # 性质：公开发行时必须能看出「这是作者原话」还是「别人的整理」
            "nature": nature_raw or "未核实",
            # 超过 200 字的原文在展示层标「节选」，提醒读者以链接为准
            "excerpt": len(en) > 200,
            "_rid": rid,
        })
    # 固定顺序：类目顺序 → 作者 → 原文，保证同一份表导出得到同一份快照。
    items.sort(key=lambda r: (CAT_ORDER[r["cat"]], r["author"], r["en"]))
    for i, r in enumerate(items):
        r["id"] = f"{r['id'].rsplit('-', 1)[0]}-{i + 1:02d}"
    for r in items:
        r.pop("_rid")

    payload = {
        "version": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
        "count": len(items),
        "items": items,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    DATA.mkdir(exist_ok=True)
    (DATA / "prompts.json").write_text(body)

    counts = {key: sum(1 for r in items if r["cat"] == key) for _, key, _ in CATS}
    natures: dict[str, int] = {}
    for item in items:
        natures[item["nature"]] = natures.get(item["nature"], 0) + 1
    meta = {
        "schema_version": 2,
        "version": payload["version"],
        "count": len(items),
        "natures": natures,
        "excerpts": sum(1 for i in items if i["excerpt"]),
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "fetched_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "source": "feishu base Mzjpb8mWoawYL9s0IuSccO4znVf / table tblnXF32xJGMYjx1",
        "cats": {key: {"name": disp, "count": counts[key]} for _, key, disp in CATS},
    }
    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")

    print(f"条目 {len(items)} 条 → {DATA/'prompts.json'}")
    print("sha256", meta["sha256"])
    for _, key, disp in CATS:
        print(f"  {disp}\t{counts[key]}")
    for p in problems:
        print("  跳过：", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "scripts/raw-20261111.ndjson"))
