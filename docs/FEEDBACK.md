# 本地反馈

```sh
psup feedback kp-verify-18 --kind useful
psup feedback kp-verify-18 --kind adopted --note "非常适合验收任务"
psup feedback-summary
```

反馈类型：

- `adopted`
- `undone`
- `useful`
- `not-useful`
- `source-broken`

记录保存到 `~/.local/share/skynet-prompt/feedback.jsonl`，可用
`SKYNET_PROMPT_FEEDBACK` 覆盖。默认只保存条目 id、类型、时间与用户主动填写的备注，不采集
会话、模型输入输出或宿主内容。
