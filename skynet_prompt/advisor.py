"""确定性的、可解释的提示词候选排序；不生成或改写正文。"""

from __future__ import annotations

from .catalog import DISPLAY
from .safety import scan_item

CATEGORY_HINTS = {
    "think_first": {
        "计划", "假设", "歧义", "不清楚", "先想", "plan", "assumption", "clarify",
    },
    "format": {
        "格式", "字数", "标签", "表格", "html", "markdown", "concise", "简洁",
    },
    "verify": {
        "验收", "测试", "验证", "检查", "完成", "test", "verify", "acceptance",
    },
    "perspective": {
        "视角", "专家", "角色", "换位", "反思", "perspective", "argue",
    },
    "form": {
        "网页", "图", "视频", "demo", "原型", "html", "可视化",
    },
    "cut": {
        "简化", "过度设计", "多余", "重构", "简洁", "simple", "scope",
    },
    "boundary": {
        "只改", "不要改", "相邻", "外科", "清理", "surgical", "boundary",
    },
    "expert_method": {
        "专业", "高手", "方法", "工具", "professional", "expert",
    },
    "outcome": {
        "结果", "目标", "不可能", "更快", "output", "outcome", "goal",
    },
}


def suggest(items: list[dict], query: str, limit: int = 5) -> list[dict]:
    if limit < 1:
        raise ValueError("limit 必须大于 0")
    terms = [term.casefold() for term in query.split() if term]
    category_matches = {
        category for category, hints in CATEGORY_HINTS.items()
        if any(term in hint for term in terms for hint in hints)
        or any(term.casefold() in hint.casefold() for term in terms for hint in hints)
    }
    results = []
    for item in items:
        verdict = (item.get("evidence") or {}).get("verdict")
        if verdict == "unverified":
            continue
        if scan_item(item)["status"] != "passed":
            continue
        haystack = " ".join((
            item.get("zh", ""),
            item.get("en", ""),
            item.get("author", ""),
            DISPLAY.get(item.get("cat", ""), ""),
        )).casefold()
        reasons = []
        score = 0.0
        for term in terms:
            if not term:
                continue
            hits = haystack.count(term)
            if hits:
                score += min(hits, 3) * 1.0
                reasons.append(f"keyword:{term}")
        if item.get("cat") in category_matches:
            score += 2.0
            reasons.append(f"category:{item['cat']}")
        if score == 0:
            continue
        if verdict == "verbatim":
            score += 1.0
            reasons.append("evidence:verbatim")
        elif verdict == "paraphrase":
            score += 0.5
            reasons.append("evidence:paraphrase")
        if item.get("cat") == "verify" and any(
            word in query.casefold() for word in ("测试", "验收", "verify")
        ):
            score += 1.0
        if score > 0:
            results.append({
                **item,
                "score": round(score, 3),
                "reasons": sorted(set(reasons)),
            })
    return sorted(
        results,
        key=lambda row: (row["score"], row["id"]),
        reverse=True,
    )[:limit]


__all__ = ["CATEGORY_HINTS", "suggest"]
