# 多语言

Pack v2 条目可以携带 `translations`：

```json
[
  {
    "language": "zh-CN",
    "text": "中文正文",
    "status": "reviewed",
    "reviewer": {"id": "reviewer"}
  }
]
```

`status` 只能是 `machine / unreviewed / reviewed`，同一 `id` 不能有重复语言。

当前官方包提供审核后的 `zh-CN` 译文，并保持 `insertion.policy = exact-zh`。其他语言缺失时
客户端明确报错，不回退生成机器翻译。
