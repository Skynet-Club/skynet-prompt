# Prompt Pack Registry

Registry 索引格式为 schema 1：

```json
{
  "schema_version": 1,
  "registry_id": "skynet-club",
  "packs": [],
  "revoked": []
}
```

每个 Pack 条目记录版本、通道、发布者、相对路径、manifest/正文 SHA-256、最小客户端版本、
发布时间和签名 key id。

```sh
python3 scripts/build_registry.py --release dist/release --out dist/registry
psup registry dist/registry/registry.json --pack official --channel dev
```

Registry 只接受已通过信任库验证的签名包。同一 `id + version` 的内容不可原地变化；内容变化
必须发布新版本。
