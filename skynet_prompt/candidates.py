"""Club 候选提交、去重和状态机。"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

STATES = (
    "candidate",
    "sourced",
    "translated",
    "reviewed",
    "published",
    "deprecated",
    "revoked",
)
TRANSITIONS = {
    "candidate": {"sourced"},
    "sourced": {"translated"},
    "translated": {"reviewed"},
    "reviewed": {"published"},
    "published": {"deprecated", "revoked"},
    "deprecated": {"revoked"},
    "revoked": set(),
}
TRACKING_QUERY = {
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src", "s", "t",
}


class CandidateError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise CandidateError("候选 URL 必须是 HTTP/HTTPS")
    host = parts.netloc.casefold()
    path = re.sub(r"/+$", "", parts.path) or "/"
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if (
            key.casefold() not in TRACKING_QUERY
            and not key.casefold().startswith("utm_")
        )
    ]
    return urlunsplit((parts.scheme.casefold(), host, path, urlencode(query), ""))


def text_fingerprint(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"\s+", " ", normalized).strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def similarity(left: str, right: str) -> float:
    norm_left = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", left)).strip().casefold()
    norm_right = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", right)).strip().casefold()
    return SequenceMatcher(None, norm_left, norm_right).ratio()


def empty_store() -> dict:
    return {"schema_version": 1, "candidates": []}


def load_store(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateError(f"候选库不可读：{path}（{exc}）") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise CandidateError("候选库 schema_version 必须是 1")
    if not isinstance(payload.get("candidates"), list):
        raise CandidateError("候选库缺少 candidates 数组")
    return payload


def save_store(path: Path, store: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def duplicate_reasons(store: dict, candidate: dict) -> list[dict]:
    url = normalize_url(candidate["url"])
    fingerprint = text_fingerprint(candidate["en"])
    matches = []
    for row in store["candidates"]:
        reasons = []
        if row.get("normalized_url") == url:
            reasons.append("same-url")
        if row.get("text_sha256") == fingerprint:
            reasons.append("same-text")
        score = similarity(row.get("en", ""), candidate["en"])
        if score >= 0.9 and "same-text" not in reasons:
            reasons.append("near-text")
        if reasons:
            matches.append({
                "id": row["id"],
                "reasons": reasons,
                "similarity": round(score, 3),
            })
    return matches


def add_candidate(store: dict, candidate: dict, *, submitted_by: str) -> dict:
    required = ("url", "author", "date", "en")
    missing = [key for key in required if not isinstance(candidate.get(key), str) or not candidate[key].strip()]
    if missing:
        raise CandidateError("候选缺少字段：" + ", ".join(missing))
    normalized_url = normalize_url(candidate["url"])
    prepared = {
        "url": candidate["url"].strip(),
        "normalized_url": normalized_url,
        "author": candidate["author"].strip(),
        "date": candidate["date"].strip(),
        "en": candidate["en"].strip(),
        "text_sha256": text_fingerprint(candidate["en"]),
    }
    duplicates = duplicate_reasons(store, prepared)
    if duplicates:
        return {"added": False, "duplicates": duplicates}

    seed = f"{normalized_url}\n{prepared['text_sha256']}".encode("utf-8")
    candidate_id = "cand-" + hashlib.sha256(seed).hexdigest()[:12]
    record = {
        "id": candidate_id,
        **prepared,
        "zh": str(candidate.get("zh") or "").strip(),
        "license": str(candidate.get("license") or "not-declared").strip(),
        "language": str(candidate.get("language") or "en").strip(),
        "status": "candidate",
        "submitted_by": submitted_by.strip(),
        "created_at": now(),
        "updated_at": now(),
        "history": [
            {
                "status": "candidate",
                "at": now(),
                "by": submitted_by.strip(),
                "note": "submitted",
            }
        ],
    }
    store["candidates"].append(record)
    return {"added": True, "candidate": record, "duplicates": []}


def transition_candidate(
    store: dict,
    candidate_id: str,
    status: str,
    *,
    by: str,
    note: str = "",
) -> dict:
    record = next(
        (row for row in store["candidates"] if row.get("id") == candidate_id),
        None,
    )
    if record is None:
        raise CandidateError(f"没有候选：{candidate_id}")
    current = record.get("status")
    if status not in TRANSITIONS.get(current, set()):
        raise CandidateError(f"非法候选状态迁移：{current} -> {status}")
    at = now()
    record["status"] = status
    record["updated_at"] = at
    record["history"].append({
        "status": status,
        "at": at,
        "by": by,
        "note": note,
    })
    return record


__all__ = [
    "CandidateError",
    "STATES",
    "add_candidate",
    "duplicate_reasons",
    "empty_store",
    "load_store",
    "normalize_url",
    "save_store",
    "similarity",
    "text_fingerprint",
    "transition_candidate",
]
