# 版权与分发字段

`skynet-prompt` 不因为来源网页公开可访问，就假定内容允许自由转载。

当前内置快照统一记录：

```json
{
  "source": {
    "license": "not-declared",
    "rights_basis": "short-quotation-with-attribution",
    "redistribution": "excerpt-only"
  }
}
```

含义：

- `license: not-declared`：本地来源快照没有取得可复用许可声明，不声称 MIT、CC 或其他授权。
- `rights_basis: short-quotation-with-attribution`：只做带作者、日期和链接的短句引用。
- `redistribution: excerpt-only`：不得把第三方全文作为正式包重新分发。

正式包发布时，结构校验会拒绝缺少 `license`、`rights_basis` 或
`redistribution` 的条目。`psup audit` 同时报告证据和版权字段的完整率。

未来接入明确许可的内容时，可以增加受控值，例如：

- `license: MIT`
- `rights_basis: explicit-license`
- `redistribution: full-text`

新增值必须同时更新 Schema、审计门和测试，不能只改一条数据。

项目自己的代码与编排使用 MIT；MIT 不覆盖第三方原文。所有正式内容必须保留作者、
日期、来源链接和版权状态，并提供来源纠错与下架路径。
