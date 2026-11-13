# 第三方发布者信任库

```sh
psup trust
psup trust-add --public-key publisher.pub.pem \
  --key-id publisher-2026 --publisher publisher-name
psup trust-revoke --key-id publisher-2026
```

登记时计算公钥 DER SHA-256 指纹。Pack 内公钥必须与 trust store 中同 key id 公钥完全一致。
撤销、过期或未知 key 均不能通过验证。

第三方发布者仍必须遵守 Pack v2、来源、许可、审核、安全和 digest 契约；信任 key 只证明发布者
身份，不替代内容审核。
