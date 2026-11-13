# Club 候选提交

Club 提交先进入候选层，不直接写正式包。

```sh
psup candidates
psup candidates --json
psup submit candidate.json --as 0@skynet-club
```

候选 JSON 最少包含：

```json
{
  "url": "https://example.com/source",
  "author": "Author",
  "date": "2026-11-12",
  "en": "Source text",
  "zh": "可选译文",
  "license": "not-declared",
  "language": "en"
}
```

提交时会：

- 规范化 URL，移除 fragment 和常见跟踪参数；
- 计算正文 SHA-256；
- 拒绝同 URL 重复；
- 拒绝正文完全相同或近似度达到 0.9 的重复；
- 生成稳定 `cand-...` id；
- 状态从 `candidate` 开始并写入历史。

状态顺序：

```text
candidate → sourced → translated → reviewed → published
```

`deprecated` 和 `revoked` 用于停止使用。候选库路径可用
`SKYNET_PROMPT_CANDIDATES` 覆盖，便于 Club 接入和测试隔离。
