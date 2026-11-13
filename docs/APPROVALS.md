# 发布审批

签名审批绑定到 Pack 的 `id / version / digest / item_count`：

```sh
psup approve --release dist/release --as reviewer@skynet.club \
  --role reviewer --private-key KEY.pem --key-id KEY_ID
psup approve --release dist/release --as publisher@skynet.club \
  --role publisher --private-key KEY.pem --key-id KEY_ID
```

stable 发布要求：

- 一个 `reviewer` 审批；
- 一个 `publisher` 审批；
- 两个审批人不同；
- 两个审批使用不同签名 key；
- 两份签名都由信任库中的 key 验证；
- 审批与最终 Pack digest 完全一致。

```sh
psup release --channel stable --private-key KEY.pem --key-id KEY_ID \
  --approval PATH/reviewer.json --approval PATH/publisher.json
```

审批签名与 Pack 签名使用同一 Ed25519 Trust 模型。审批只覆盖它创建时的 Pack 摘要；内容变化
后旧审批自动失效。
