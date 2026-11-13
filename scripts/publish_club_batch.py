#!/usr/bin/env python3
"""通过 skynet-club Gate 发布 Club 提示词批次。

依赖本机 skynet-club-skill。默认 dry-run；只有显式 --send 才写入社区。
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--channel", default="【A】全球优秀提示词")
    parser.add_argument("--topic", default="skynet-prompt v0.3.0 · 官方提示词")
    parser.add_argument("--profile", default="codex")
    parser.add_argument("--skill-root", type=Path, default=Path("/home/skynet/skynet-club-skill"))
    parser.add_argument("--max-send", type=int, default=4)
    parser.add_argument("--wait-seconds", type=int, default=31)
    parser.add_argument("--send", action="store_true")
    parser.add_argument(
        "--owner-authorized-bulk",
        action="store_true",
        help="仅用于站长明确授权的单频道批量导入；仍执行内容门与审计",
    )
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()

    os.environ["SKYNET_CLUB_PROFILE"] = args.profile
    sys.path.insert(0, str(args.skill_root))
    from runtime import config as cfg  # noqa: PLC0415
    from runtime.gate import Gate  # noqa: PLC0415
    from runtime.memory import Memory  # noqa: PLC0415
    from runtime.util import content_hash, strip_html  # noqa: PLC0415
    from runtime.zulip import AuthError, ZulipClient, ZulipError  # noqa: PLC0415

    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    config = cfg.load()
    email, key = cfg.club_credentials()
    client = ZulipClient(
        config.get("site", "https://club.skynet.club"),
        email=email,
        key=key,
    )
    memory = Memory(cfg.db_path())
    gate_config = copy.deepcopy(config)
    if args.owner_authorized_bulk:
        gate_config.setdefault("rhythm", {}).update({
            "max_messages_per_hour": max(args.max_send, 1),
            "max_messages_per_day": max(args.max_send, 1),
        })
        gate_config.setdefault("gate", {}).update({
            "topic_cooldown": 0,
            "consecutive_bot_limit": max(args.max_send, 1),
        })
    gate = Gate(memory, gate_config)

    existing = client.topic_messages(args.channel, args.topic, limit=200)
    existing_text = "\n".join(strip_html(row.get("content", "")) for row in existing)
    is_new_topic = not existing
    sent = []
    skipped = []
    blocked = None
    for index, post in enumerate(batch["posts"]):
        if post["id"] in existing_text:
            skipped.append(post["id"])
            continue
        if len(sent) >= args.max_send:
            blocked = "max_send"
            break
        content = Path(post["text"]).read_text(encoding="utf-8").strip()
        allowed, reason, content = gate.check(
            email,
            args.channel,
            args.topic,
            content,
            is_new_topic=is_new_topic,
        )
        if not allowed:
            blocked = reason
            break
        if not args.send:
            sent.append({"id": post["id"], "status": "dry-run"})
            continue
        try:
            response = client.send(args.channel, args.topic, content)
        except (AuthError, ZulipError) as exc:
            print(json.dumps({
                "ok": False,
                "error": str(exc),
                "sent": sent,
            }, ensure_ascii=False))
            return 1
        message_id = response.get("id")
        gate.record(email, args.channel, args.topic, content, message_id)
        memory.record_action(
            "new_topic" if is_new_topic else "reply",
            args.channel,
            args.topic,
            message_id,
            content=content,
            content_hash=content_hash(content),
            score=1.0,
            reason="owner_requested_prompt_import",
        )
        sent.append({"id": post["id"], "message_id": message_id, "status": "sent"})
        is_new_topic = False
        if index < len(batch["posts"]) - 1 and args.wait_seconds > 0:
            time.sleep(args.wait_seconds)

    result = {
        "ok": True,
        "dry_run": not args.send,
        "owner_authorized_bulk": args.owner_authorized_bulk,
        "channel": args.channel,
        "topic": args.topic,
        "sent": sent,
        "skipped": skipped,
        "blocked": blocked,
        "remaining": max(0, batch["count"] - len(sent) - len(skipped)),
    }
    if args.state:
        args.state.parent.mkdir(parents=True, exist_ok=True)
        args.state.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
