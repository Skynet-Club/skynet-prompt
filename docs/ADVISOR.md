# 独立 Advisor

```sh
psup suggest 验收 测试 --limit 5
psup suggest 验收 测试 --limit 5 --json
```

Advisor 使用确定性关键词和类目规则排序，并显示 `keyword / category / evidence` 原因。

- 只建议 `verbatim` 与 `paraphrase` 条目；
- 不推荐 `unverified` 条目；
- 自动排除安全扫描命中的条目；
- 不生成、不翻译、不改写正文；
- 用户选定后仍调用 `psup print <id>` 原样插入。
