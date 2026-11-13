# 来源、翻译与安全审核

正式内容的审核决定保存在 `reviews/review-decisions.json`，生成后的账本为
`reviews/review-ledger.json`。

```sh
python3 scripts/build_review_ledger.py
psup reviews
psup reviews --json
```

每条审核记录绑定到内容摘要，包含：

- 来源审核状态；
- 翻译审核状态；
- 安全审核状态；
- 审核者身份与类型；
- 方法与时间；
- 条目摘要。

正文、中文译文或来源变化后，`item_sha256` 不再匹配，旧审核自动失效。

当前审核者如实标记为 `codex-agent / ai-assisted`，不冒充人工审核。未核实条目不能进入
审核账本，也不能进入正式包。
