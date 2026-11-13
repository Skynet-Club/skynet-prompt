# Pack 签名

Pack v2 使用 Ed25519 对 manifest 签名。签名 payload 是移除 `signature` 后的 Canonical JSON：

- UTF-8；
- 键排序；
- 紧凑分隔符；
- `ensure_ascii=false`。

签名对象：

```json
{
  "algorithm": "ed25519",
  "key_id": "skynet-club-dev-2026-11",
  "public_key_pem": "...",
  "value": "base64-signature"
}
```

验证必须同时满足：

- manifest 内容未被修改；
- Pack 内公钥与信任库记录一致；
- key id 存在且状态允许；
- 信任库公钥指纹匹配。

开发签名：

```sh
psup release --channel dev \
  --private-key ~/.config/skynet-prompt/keys/skynet-club-dev.pem \
  --key-id skynet-club-dev-2026-11
```

私钥不进入仓库。公开公钥与元数据位于 `trust/`。
