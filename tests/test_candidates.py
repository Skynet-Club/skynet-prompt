"""Club 候选提交与去重测试。"""

from __future__ import annotations

from skynet_prompt.candidates import (
    add_candidate,
    duplicate_reasons,
    empty_store,
    normalize_url,
    similarity,
    text_fingerprint,
    transition_candidate,
)


def _candidate(**overrides) -> dict:
    row = {
        "url": "https://Example.com/article/?utm_source=test&id=1#section",
        "author": "Author",
        "date": "2026-11-12",
        "en": "Define the acceptance check before implementation.",
        "zh": "实现前先定义验收检查。",
        "license": "not-declared",
        "language": "en",
    }
    row.update(overrides)
    return row


def test_url_normalization_removes_fragment_and_tracking():
    assert normalize_url(_candidate()["url"]) == "https://example.com/article?id=1"


def test_same_url_is_rejected():
    store = empty_store()
    first = add_candidate(store, _candidate(), submitted_by="agent")
    assert first["added"] is True

    duplicate = add_candidate(
        store,
        _candidate(url="https://example.com/article?id=1"),
        submitted_by="agent",
    )
    assert duplicate["added"] is False
    assert "same-url" in duplicate["duplicates"][0]["reasons"]


def test_near_text_is_flagged():
    store = empty_store()
    add_candidate(store, _candidate(), submitted_by="agent")
    variant = _candidate(
        url="https://example.com/another",
        en="Define the acceptance check before implementing it.",
    )
    matches = duplicate_reasons(store, variant)
    assert matches
    assert "near-text" in matches[0]["reasons"]
    assert similarity(variant["en"], _candidate()["en"]) >= 0.9


def test_normalized_text_fingerprint_is_stable():
    left = text_fingerprint("State   your assumptions.\nIf uncertain, ask.")
    right = text_fingerprint(" state your assumptions. If uncertain, ask. ")
    assert left == right


def test_candidate_starts_in_candidate_state():
    store = empty_store()
    result = add_candidate(store, _candidate(), submitted_by="0@skynet-club")
    record = result["candidate"]
    assert record["status"] == "candidate"
    assert record["submitted_by"] == "0@skynet-club"
    assert record["history"][0]["status"] == "candidate"
    assert len(record["text_sha256"]) == 64


def test_candidate_transitions_publish_path():
    store = empty_store()
    record = add_candidate(store, _candidate(), submitted_by="agent")["candidate"]
    for status in ("sourced", "translated", "reviewed", "published"):
        record = transition_candidate(
            store,
            record["id"],
            status,
            by="agent",
            note=status,
        )
    assert record["status"] == "published"
    assert [row["status"] for row in record["history"]] == [
        "candidate", "sourced", "translated", "reviewed", "published",
    ]
