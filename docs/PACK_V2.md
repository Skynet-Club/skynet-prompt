# Prompt Pack v2

v2 是 Club 策展、发布流水线和 Registry 共用的包契约。v1 本地包继续兼容，但 v2 包在加载时执行严格校验。

机器可读定义：

- `schemas/prompt-pack-v2.schema.json`
- `schemas/prompts-v2.schema.json`
- `skynet_prompt/pack_schema.py`

## Manifest

必需字段：

```text
schema_version
id
name
version
channel
published_at
items
sha256
digest
publisher
min_client_version
license_summary
require_evidence
```

发布通道只有 `dev`、`canary`、`stable`。`signature` 当前允许为 `null`，M2 接入签名后正式通道将要求有效签名。

## 条目

除了 v1 的正文与作者字段，每条还必须包含：

- `source.quote/url/author/published_at/language`
- `source.license/rights_basis/redistribution`
- `source.snapshot_sha256`
- `evidence.verdict/checked_at`
- `review.source/translation/safety`
- `safety.status/flags`
- `insertion.policy: exact-zh`

`review` 与 `safety` 明确允许 `unreviewed`。未审核条目可以进入实验包，但不能被标记为正式审核通过。

## 校验入口

```sh
python3 scripts/test.py
python3 scripts/export_official.py --out /tmp/official
SKYNET_PROMPT_DATA=/tmp/official psup audit --json
```
